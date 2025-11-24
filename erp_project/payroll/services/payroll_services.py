import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from django.db import transaction
from human_resources.hr_models import Employees
from ..payroll_models import DailyZiGRateToUSD, Payroll
from ..repositories.payroll_repository import PayrollRepository, TaxRepository


class PayrollService:

    AIDS_LEVY_RATE = Decimal("0.03")
    # NSSA_RATE = Decimal("0.09") # This is redundant
    NSSA_EMPLOYEE_RATE = Decimal("0.045")
    NSSA_EMPLOYER_RATE = Decimal("0.045")
    
    @staticmethod
    def calculate_tax(salary, brackets):
        """
        Corrected tax calculation for a (Salary * Rate) - Deduction style table.
        Finds the single correct bracket for the given salary.
        
        - salary: Decimal
        - brackets: iterable of (min_income, max_income_or_none, rate, deduction)
        Returns: (paye_decimal, aids_levy_decimal)
        """
        try:
            salary = Decimal(salary)
        except (InvalidOperation, TypeError):
            salary = Decimal("0.00")

        if salary <= 0:
            return Decimal("0.00"), Decimal("0.00")

        paye = Decimal("0.00")
        
        # Normalize and sort brackets by min_income
        normalized_brackets = []
        for b in brackets:
            min_inc, max_inc, rate, deduct = b
            normalized_brackets.append((
                Decimal(min_inc or 0),
                None if max_inc in (None, "None", "") else Decimal(max_inc),
                Decimal(rate or 0),
                Decimal(deduct or 0)
            ))
        
        # Sort by min_income descending to find the correct bracket first
        normalized_brackets.sort(key=lambda x: x[0], reverse=True)

        for min_inc, max_inc, rate, deduct in normalized_brackets:
            # Check if salary falls into this bracket
            if salary > min_inc:
                # This is the correct bracket. Calculate PAYE and stop.
                paye = (salary * rate) - deduct
                break
        
        # Ensure PAYE is not negative
        paye = max(Decimal("0.00"), paye)
        
        # AIDS levy = 3% of PAYE
        aids = (paye * PayrollService.AIDS_LEVY_RATE)

        # Quantize results to 2 decimal places
        paye_rounded = paye.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        aids_rounded = aids.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return paye_rounded, aids_rounded

    @staticmethod
    def calculate_nssa(salary):
        """
        Compute NSSA split between employee and employer
        
        FIXED: The original logic was (salary * 0.09) * 0.045, which is incorrect.
        """
        # TODO: Add NSSA insurable earnings ceiling (maximum salary) logic here
        # Example: nssa_base = min(salary, MAX_NSSA_SALARY)
        nssa_base = salary # Assuming no ceiling for this example
        
        employee_nssa = nssa_base * PayrollService.NSSA_EMPLOYEE_RATE
        employer_nssa = nssa_base * PayrollService.NSSA_EMPLOYER_RATE
        
        return employee_nssa, employer_nssa

    @staticmethod
    def compute_allowances(employee):
        """
        Sum all allowances for the employee in USD and ZiG
        
        FIXED: Assumes 'employee.allowances' is a related manager from a model
        (e.g., EmployeeAllowance) that has 'amount' and 'currency' fields.
        """
        total_usd = Decimal("0.00")
        total_zig = Decimal("0.00")

        # We must use the cleaned models (e.g., EmployeeAllowance) for this to work
        for allowance in employee.allowances.all():
            if allowance.currency == 'USD':
                total_usd += allowance.amount
            elif allowance.currency == 'ZIG':
                total_zig += allowance.amount
                
        return total_usd, total_zig

    @staticmethod
    def compute_deductions(employee):
        """
        Sum all deductions for the employee in USD and ZiG
        
        FIXED: Assumes 'employee.deductions' is a related manager from a model
        (e.g., EmployeeDeduction) that has 'amount' and 'currency' fields.
        """
        total_usd = Decimal("0.00")
        total_zig = Decimal("0.00")

        for deduction in employee.deductions.all():
            if deduction.currency == 'USD':
                total_usd += deduction.amount
            elif deduction.currency == 'ZIG':
                total_zig += deduction.amount
                
        return total_usd, total_zig
    
    
    @staticmethod
    def get_latest_zig_to_usd_rate():
        """
        Fetch the latest ZiG to USD exchange rate from DailyZiGRateToUSD
        
        FIXED: Raises a specific error if no rate is found.
        """
        latest_rate = DailyZiGRateToUSD.objects.order_by('-date').first()
        if latest_rate and latest_rate.average > 0:
            return latest_rate.average
        
        # Do not allow payroll to run with a missing or zero rate
        raise ValueError("No valid ZiG to USD exchange rate found in the system.")
    
    
    @staticmethod
    @transaction.atomic
    def process_payroll_for_period(period_str):
        # Convert "2025-09" → 2025-09-01
        try:
            period_date = datetime.datetime.strptime(period_str + "-01", "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid period format. Use YYYY-MM."}

        # Use the correct model 'Employees' and 'is_active'
        employees = Employees.objects.filter(is_active=True) 
        processed = []
        skipped = []
        errors = []

        for employee in employees:
            try:
                # Check existing payrolls for the period
                if Payroll.objects.filter(
                    employee=employee, 
                    period__year=period_date.year, 
                    period__month=period_date.month
                ).exists():
                    skipped.append(employee.employee_id)
                    continue

                PayrollService.create_employee_payroll(employee, period_date)
                processed.append(employee.employee_id)
            
            except Exception as e:
                # Catch errors (like missing rate) and report them
                errors.append({"employee_id": employee.employee_id, "error": str(e)})

        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total_processed": len(processed),
            "total_skipped": len(skipped),
            "total_errors": len(errors),
        }
        
        
    @staticmethod
    @transaction.atomic
    def create_employee_payroll(employee, period):
        # This function now expects 'get_latest_zig_to_usd_rate'
        # to raise an error if no rate is found, which will be
        # caught by the 'process_payroll_for_period' loop.
        
        zig_to_usd_rate = PayrollService.get_latest_zig_to_usd_rate()

        usd_brackets = TaxRepository.get_brackets("USD", period)
        zig_brackets = TaxRepository.get_brackets("ZIG", period)

        usd_salary = employee.usd_salary or Decimal("0")
        zig_salary = employee.zig_salary or Decimal("0")

        # Convert ZiG salary to USD for tax calculation
        zig_salary_usd = (zig_salary * zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # PAYE + AIDS
        usd_paye, usd_aids = PayrollService.calculate_tax(usd_salary, usd_brackets)
        # We calculate ZiG tax based on its USD equivalent
        zig_paye_usd, zig_aids_usd = PayrollService.calculate_tax(zig_salary_usd, zig_brackets)

        # NSSA
        usd_nssa_emp, usd_nssa_employer = PayrollService.calculate_nssa(usd_salary)
        zig_nssa_emp_usd, zig_nssa_employer_usd = PayrollService.calculate_nssa(zig_salary_usd)

        # Allowances & Deductions
        allowances_usd, allowances_zig = PayrollService.compute_allowances(employee)
        deductions_usd, deductions_zig = PayrollService.compute_deductions(employee)
        
        # Convert ZiG allowances/deductions to USD equivalent for net calculation
        allowances_zig_usd = (allowances_zig * zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        deductions_zig_usd = (deductions_zig * zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Net Salaries
        usd_net = usd_salary - usd_paye - usd_nssa_emp - usd_aids + allowances_usd - deductions_usd
        zig_net_usd = zig_salary_usd - zig_paye_usd - zig_nssa_emp_usd - zig_aids_usd + allowances_zig_usd - deductions_zig_usd
        
        # Convert net ZiG back to ZiG currency
        zig_net = (zig_net_usd / zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return PayrollRepository.create_payroll(
            employee=employee,
            period=period,
            base_salary_usd=usd_salary,
            net_salary_usd=usd_net,
            base_salary_zig=zig_salary,
            net_salary_zig=zig_net,
            exchange_rate=zig_to_usd_rate,
            status="Draft",
            notes="Generated by PayrollService",
            paye_usd=usd_paye,
            paye_zig=(zig_paye_usd / zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            aids_levy_usd=usd_aids,
            aids_levy_zig=(zig_aids_usd / zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            nssa_employee_usd=usd_nssa_emp,
            nssa_employer_usd=usd_nssa_employer,
            nssa_employee_zig=(zig_nssa_emp_usd / zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            nssa_employer_zig=(zig_nssa_employer_usd / zig_to_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_allowances_usd=allowances_usd,
            total_allowances_zig=allowances_zig,
            total_deductions_usd=deductions_usd,
            total_deductions_zig=deductions_zig,
        )
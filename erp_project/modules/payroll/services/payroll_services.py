from erp.dependencies import *

class PayrollService:

    AIDS_LEVY_RATE = Decimal("0.03")
    NSSA_RATE = Decimal("0.09")  # Total rate
    NSSA_EMPLOYEE_RATE = Decimal("0.045")
    NSSA_EMPLOYER_RATE = Decimal("0.045")
    
    @staticmethod
    def calculate_tax(salary, brackets):
        """
        Progressive tax calculation:
        - salary: Decimal
        - brackets: iterable of (min_income, max_income_or_none, rate, deduction)
          where min_income, max_income, rate, deduction can be Decimal or convertible
        Returns: (paye_decimal, aids_levy_decimal)
        """
        try:
            salary = Decimal(salary)
        except (InvalidOperation, TypeError):
            salary = Decimal("0.00")

        if salary <= 0:
            return Decimal("0.00"), Decimal("0.00")

        # normalize and sort brackets by min_income
        normalized = []
        for b in brackets:
            # Accept both tuples of length 3 or 4, but expect 4
            if len(b) == 4:
                min_inc, max_inc, rate, deduct = b
            elif len(b) == 3:
                min_inc, max_inc, rate = b
                deduct = Decimal("0.00")
            else:
                # skip invalid bracket entry
                continue

            min_inc = Decimal(min_inc or 0)
            max_inc = None if max_inc in (None, "None", "") else Decimal(max_inc)
            rate = Decimal(rate)
            deduct = Decimal(deduct or 0)
            normalized.append((min_inc, max_inc, rate, deduct))

        # sort by min_income ascending
        normalized.sort(key=lambda x: x[0])

        paye = Decimal("0.00")
        remaining = salary

        for min_inc, max_inc, rate, deduct in normalized:
            # If salary is below the bracket min, skip
            if salary <= min_inc:
                break

            # bracket lower bound is min_inc, upper bound is max_inc (or infinity)
            upper = max_inc if max_inc is not None else Decimal("Infinity")

            # taxable portion in this bracket:
            # it is the amount between min_inc and upper, but not exceeding salary
            portion = min(salary, upper) - min_inc
            if portion <= 0:
                continue

            # tax for this portion before deduction
            portion_tax = (portion * rate) - deduct

            # ensure we don't subtract too much (deduction shouldn't cause negative tax)
            portion_tax = max(portion_tax, Decimal("0.00"))

            paye += portion_tax

            # if salary <= upper, we finished taxing all income
            if salary <= upper:
                break

        # AIDS levy = 3% of PAYE
        aids = (paye * PayrollService.AIDS_LEVY_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # round PAYE
        paye = paye.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return paye, aids

    @staticmethod
    def calculate_nssa(salary):
        """
        Compute NSSA split between employee and employer
        """
        total = salary * PayrollService.NSSA_RATE
        return total * PayrollService.NSSA_EMPLOYEE_RATE, total * PayrollService.NSSA_EMPLOYER_RATE

    @staticmethod
    def compute_allowances(employee):
        """
        Sum all allowances for the employee in USD and ZiG
        """
        total_usd = sum([a.amount for a in employee.allowances.all()])
        total_zig = sum([a.amount for a in employee.allowances.all()])  # Assuming stored in ZiG if needed
        return Decimal(total_usd), Decimal(total_zig)

    @staticmethod
    def compute_deductions(employee):
        """
        Sum all deductions for the employee in USD and ZiG
        """
        total_usd = sum([d.amount for d in employee.deductions.all()])
        total_zig = sum([d.amount for d in employee.deductions.all()])
        return Decimal(total_usd), Decimal(total_zig)
    
    
    @staticmethod
    def get_latest_zig_to_usd_rate():
        """
        Fetch the latest ZiG to USD exchange rate from DailyZiGRateToUSD
        """
        latest_rate = DailyZiGRateToUSD.objects.order_by('-date').first()
        if latest_rate:
            return latest_rate.average
        return latest_rate
    
    
    @staticmethod
    @transaction.atomic
    def process_payroll_for_period(period_str):
        # Convert "2025-09" → 2025-09-01
        period_date = datetime.strptime(period_str + "-01", "%Y-%m-%d").date()

        employees = Employees.objects.filter(isActive=True)
        processed = []
        skipped = []

        for employee in employees:
            # Check existing payrolls for the period
            if Payroll.objects.filter(employee=employee, period__year=period_date.year, period__month=period_date.month).exists():
                skipped.append(employee.employeeid)
                continue

            PayrollService.create_employee_payroll(employee, period_date)
            processed.append(employee.employeeid)

        return {
            "processed": processed,
            "skipped": skipped,
            "total_processed": len(processed),
            "total_skipped": len(skipped)
        }
        
        
    @staticmethod
    @transaction.atomic
    def create_employee_payroll(employee, period):
        usd_brackets = TaxRepository.get_brackets("USD", period)
        zig_brackets = TaxRepository.get_brackets("ZiG", period)

        usd_salary = employee.usd_salary or Decimal("0")
        zig_salary = employee.zig_salary or Decimal("0")

        zig_to_usd_rate = PayrollService.get_latest_zig_to_usd_rate()
        zig_salary_usd = zig_salary * zig_to_usd_rate

        # PAYE + AIDS
        usd_paye, usd_aids = PayrollService.calculate_tax(usd_salary, usd_brackets)
        zig_paye_usd, zig_aids_usd = PayrollService.calculate_tax(zig_salary_usd, zig_brackets)

        # NSSA
        usd_nssa_emp, usd_nssa_employer = PayrollService.calculate_nssa(usd_salary)
        zig_nssa_emp_usd, zig_nssa_employer_usd = PayrollService.calculate_nssa(zig_salary_usd)

        # Allowances & Deductions
        allowances_usd, allowances_zig = PayrollService.compute_allowances(employee)
        deductions_usd, deductions_zig = PayrollService.compute_deductions(employee)
        
        # Net Salaries
        usd_net = usd_salary - usd_paye - usd_nssa_emp - usd_aids + allowances_usd - deductions_usd
        zig_net_usd = zig_salary_usd - zig_paye_usd - zig_nssa_emp_usd - zig_aids_usd + allowances_zig*zig_to_usd_rate - deductions_zig*zig_to_usd_rate
        zig_net = zig_net_usd / zig_to_usd_rate if zig_to_usd_rate else Decimal("0.0")

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
            paye_zig=zig_paye_usd / zig_to_usd_rate,
            aids_levy_usd=usd_aids,
            aids_levy_zig=zig_aids_usd / zig_to_usd_rate,
            nssa_employee_usd=usd_nssa_emp,
            nssa_employer_usd=usd_nssa_employer,
            nssa_employee_zig=zig_nssa_emp_usd / zig_to_usd_rate,
            nssa_employer_zig=zig_nssa_employer_usd / zig_to_usd_rate,
            total_allowances_usd=allowances_usd,
            total_allowances_zig=allowances_zig,
            total_deductions_usd=deductions_usd,
            total_deductions_zig=deductions_zig,
        )

from datetime import datetime
from django.db import transaction
from django.utils.timezone import now
from django.conf import settings
from ..models import (
    Employees, Payroll, ZiGRateToUSD,
    EmployeeDeductables, NSSACap, PensionFund, TaxBracket
)

class PayrollProcessor:
    @staticmethod
    def get_current_rate():
        print("[PayrollProcessor] Fetching current exchange rate...")
        # Get the most recent rate
        return ZiGRateToUSD.objects.order_by('-date').first()

    @staticmethod
    def calculate_tax(amount, brackets):
        print(f"[PayrollProcessor] Calculating tax for amount: {amount} with brackets: {brackets}")
        if not brackets:
            print("[PayrollProcessor] No tax brackets provided for calculation.")
            return 0.0

        tax_payable = 0.0
        # Ensure brackets are sorted by upper limit for correct calculation
        sorted_brackets = sorted(brackets, key=lambda x: x[0])

        for upper, rate, deduct in sorted_brackets:
            if amount <= upper:
                base_tax = amount * rate - deduct
                base_tax = max(base_tax, 0) # Tax cannot be negative
                aids_levy = base_tax * 0.03 # 3% AIDS Levy
                total_tax = round(base_tax + aids_levy, 2)
                print(f"[PayrollProcessor] Tax breakdown - Base: {base_tax}, AIDS Levy: {aids_levy}, Total: {total_tax}")
                return total_tax
        return 0.0 # Should ideally not be reached if max_income is inf for last bracket

    @staticmethod
    def get_nssa_contribution(salary: float, currency: str, period: datetime.date) -> dict:
        print(f"[PayrollProcessor] NSSA Calculation - salary: {salary}, currency: {currency}")
        
        # Get the latest active NSSA cap for the period
        nssa_cap_obj = NSSACap.objects.filter(active_from__lte=period).order_by('-active_from').first()
        
        if not nssa_cap_obj:
            print("[PayrollProcessor] No NSSA Cap record found for period. Returning 0.")
            return {
                "currency": currency,
                "pensionable_earnings": 0.0,
                "employee_nssa": 0.0,
                "employer_nssa": 0.0,
                "total_nssa": 0.0
            }

        rate = float(nssa_cap_obj.rate)
        
        # Determine the ceiling based on currency
        ceiling = 0.0
        if currency.upper() == "USD":
            ceiling = float(nssa_cap_obj.usd_cap)
        elif currency.upper() == "ZWL" or currency.upper() == "ZIG": # Using ZIG to match current context
            ceiling = float(nssa_cap_obj.zwl_cap) # Assuming zwl_cap now represents ZiG cap
        else:
            print(f"[PayrollProcessor] Unsupported NSSA currency: {currency}")
            return {
                "currency": currency,
                "pensionable_earnings": 0.0,
                "employee_nssa": 0.0,
                "employer_nssa": 0.0,
                "total_nssa": 0.0
            }

        pensionable = min(salary, ceiling)
        employee_nssa = 0.0
        employer_nssa = 0.0

        if nssa_cap_obj.contribution_type in ["employee", "employee_and_employer"]:
            employee_nssa = round(pensionable * rate, 2)
        if nssa_cap_obj.contribution_type in ["employer", "employee_and_employer"]:
            employer_nssa = round(pensionable * rate, 2)

        result = {
            "currency": currency,
            "pensionable_earnings": pensionable,
            "employee_nssa": employee_nssa,
            "employer_nssa": employer_nssa,
            "total_nssa": round(employee_nssa + employer_nssa, 2)
        }
        print(f"[PayrollProcessor] NSSA result: {result}")
        return result

    @staticmethod
    def get_pension_contribution(employee_deduction, salary, currency):
        print(f"[PayrollProcessor] Calculating pension for {currency} salary: {salary}")
        if not employee_deduction or not employee_deduction.pension_fund:
            print("[PayrollProcessor] No active pension deduction found for employee.")
            return 0.0
        
        pension = employee_deduction.pension_fund
        
        # Check if the pension fund applies to the current currency
        if pension.currency != currency.lower() and pension.currency != "both":
            print(f"[PayrollProcessor] Pension fund '{pension.name}' does not match currency '{currency}'.")
            return 0.0
            
        if not employee_deduction.pension_employee_contribution:
            print("[PayrollProcessor] Employee pension contribution not active for this fund.")
            return 0.0
            
        rate = float(pension.employee_rate)
        contribution = round(float(salary) * rate, 2)
        print(f"[PayrollProcessor] Pension contribution: {contribution}")
        return contribution

    @staticmethod
    @transaction.atomic
    def create_employee_payroll(employee, period):
        print(f"\n[PayrollProcessor] Creating payroll for employee: {employee.employeeid}, period: {period}")

        # Get relevant tax brackets for the period
        usd_tax_brackets = Payroll.load_tax_brackets("USD", period)
        zig_tax_brackets = Payroll.load_tax_brackets("ZWG", period) # Use ZWG as per your model choices

        try:
            exchange_rate_obj = ZiGRateToUSD.objects.filter(date__lte=period).order_by('-date').first()
            exchange_rate = float(exchange_rate_obj.rate) if exchange_rate_obj and exchange_rate_obj.rate is not None else 0.005
            print(f"[PayrollProcessor] Exchange rate used: {exchange_rate}")
        except Exception as e:
            print(f"[PayrollProcessor] Error fetching exchange rate: {e}. Using default.")
            exchange_rate = 0.005

        deducts = EmployeeDeductables.objects.filter(employee=employee, active=True).first()

        # USD Calculations
        usd_salary = float(employee.usd_salary or 0)
        usd_tax = PayrollProcessor.calculate_tax(usd_salary, usd_tax_brackets)

        usd_nssa_data = PayrollProcessor.get_nssa_contribution(usd_salary, "USD", period)
        usd_nssa = usd_nssa_data['employee_nssa'] # Extract employee portion

        usd_pension = PayrollProcessor.get_pension_contribution(deducts, usd_salary, "USD")
        
        usd_net = max(usd_salary - usd_tax - usd_nssa - usd_pension, 0)
        print(f"[PayrollProcessor] USD: gross={usd_salary}, tax={usd_tax}, nssa={usd_nssa}, pension={usd_pension}, net={usd_net}")

        # ZIG Calculations
        zig_salary = float(employee.zig_salary or 0)
        zig_tax = PayrollProcessor.calculate_tax(zig_salary, zig_tax_brackets)

        zig_nssa_data = PayrollProcessor.get_nssa_contribution(zig_salary, "ZWG", period) # Use ZWG here
        zig_nssa = zig_nssa_data['employee_nssa'] # Extract employee portion

        zig_pension = PayrollProcessor.get_pension_contribution(deducts, zig_salary, "ZWL") # Currency for get_pension_contribution matches model choice
        
        zig_net = max(zig_salary - zig_tax - zig_nssa - zig_pension, 0)
        print(f"[PayrollProcessor] ZIG: gross={zig_salary}, tax={zig_tax}, nssa={zig_nssa}, pension={zig_pension}, net={zig_net}")

        payroll = Payroll.objects.create(
            employee=employee,
            period=period,
            base_salary_usd=usd_salary,
            net_salary_usd=usd_net,
            tax_usd=usd_tax,
            nssa_usd=usd_nssa,
            pension_usd=usd_pension,

            base_salary_zig=zig_salary,
            net_salary_zig=zig_net,
            tax_zig=zig_tax,
            nssa_zig=zig_nssa,
            pension_zig=zig_pension,

            exchange_rate=exchange_rate,
            status='Draft',
            notes='Auto-generated payroll',
        )
        print(f"[PayrollProcessor] Payroll created for {employee.employeeid}")
        return payroll

    @staticmethod
    def create_monthly_payroll(period):
        print(f"\n[PayrollProcessor] Generating payroll for period: {period}")
        if not period:
            period = now().replace(day=1).date()
        else:
            period = period.replace(day=1)
        print(f"[PayrollProcessor] Normalized period: {period}")

        employees = Employees.objects.filter(isActive=True)
        count = 0

        for emp in employees:
            print(f"\n[PayrollProcessor] Processing employee: {emp.employeeid}")
            if Payroll.objects.filter(employee=emp, period=period).exists():
                print("[PayrollProcessor] Payroll already exists, skipping")
                continue

            PayrollProcessor.create_employee_payroll(emp, period)
            count += 1

        print(f"[PayrollProcessor] Payroll generation complete. Total new records: {count}")
        return count
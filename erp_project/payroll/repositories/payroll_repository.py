from ..payroll_models import Payroll, DailyZiGRateToUSD, TaxBracket
from human_resources.hr_models import Employees

class PayrollRepository:

    @staticmethod
    def get_by_employee_and_period(employee, period):
        return Payroll.objects.filter(employee=employee, period=period).first()

    @staticmethod
    def create_payroll(**kwargs):
        return Payroll.objects.create(**kwargs)

    @staticmethod
    def list_employees():
        return Employees.objects.filter(isActive=True)

class ExchangeRateRepository:
    @staticmethod
    def get_latest(date):
        return DailyZiGRateToUSD.objects.filter(date__lte=date).order_by('-date').first()

class TaxRepository:
    @staticmethod
    def get_brackets(currency, period):
        """
        Get the most recent tax brackets for the given currency that are active for this period.
        Returns a list of tuples: (min_income, max_income, rate, deduction)
        """
        # First, find the most recent active_from date that is <= period
        latest_bracket = TaxBracket.objects.filter(
            currency=currency,
            active_from__lte=period
        ).order_by("-active_from").first()

        if not latest_bracket:
            return []

        # Get all brackets with that active_from date
        brackets = TaxBracket.objects.filter(
            currency=currency,
            active_from=latest_bracket.active_from
        ).order_by("min_income")

        # Return as list of tuples for calculate_tax function
        return [
            (b.min_income, b.max_income, b.rate, b.deduction)
            for b in brackets
        ]
    
# class NSSARepository:
#     @staticmethod
#     def get_cap(period):
#         return NSSACap.objects.filter(active_from__lte=period).order_by('-active_from').first()

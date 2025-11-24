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
        return TaxBracket.objects.filter(currency=currency, active_from=period).order_by("max_income")
    
# class NSSARepository:
#     @staticmethod
#     def get_cap(period):
#         return NSSACap.objects.filter(active_from__lte=period).order_by('-active_from').first()

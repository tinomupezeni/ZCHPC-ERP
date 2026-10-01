from modules.hr.infrastructure.persistence.models import Employees
from modules.payroll.infrastructure.persistence.models import PayrollProfile, EmployeeBankAccount, StatutoryProfile

class EmployeeOrchestrator:
    @staticmethod
    def get_full_profile(uuid):
        try:
            employee = Employees.objects.get(uuid=uuid)
        except Employees.DoesNotExist:
            return None
            
        payroll_profile = PayrollProfile.objects.filter(employee=employee).first()
        bank_account = EmployeeBankAccount.objects.filter(employee=employee, is_primary=True).first()
        if not bank_account:
            bank_account = EmployeeBankAccount.objects.filter(employee=employee).first()
            
        statutory_profile = StatutoryProfile.objects.filter(employee=employee).first()
        
        return {
            # HR
            "uuid": employee.uuid,
            "employee_id": employee.employee_id,
            "first_name": employee.first_name,
            "surname": employee.surname,
            "email": employee.email,
            "phone": employee.phone,
            
            # Payroll
            "usd_salary": payroll_profile.usd_salary if payroll_profile else None,
            "zig_salary": payroll_profile.zig_salary if payroll_profile else None,
            "pay_frequency": payroll_profile.pay_frequency if payroll_profile else None,
            
            # Bank
            "bank_name": bank_account.bank_name if bank_account else None,
            "bank_account": bank_account.account_number if bank_account else None,
            
            # Statutory
            "nssa_number": statutory_profile.nssa_number if statutory_profile else None,
            "zimra_tax_number": statutory_profile.zimra_tax_number if statutory_profile else None,
            "paye_number": statutory_profile.paye_number if statutory_profile else None,
        }

    @staticmethod
    def update_full_profile(uuid, data):
        from django.db import transaction
        
        try:
            with transaction.atomic():
                employee = Employees.objects.get(uuid=uuid)
                
                # 1. Update HR fields
                if 'first_name' in data: employee.first_name = data['first_name']
                if 'surname' in data: employee.surname = data['surname']
                if 'email' in data: employee.email = data['email']
                if 'phone' in data: employee.phone = data['phone']
                employee.save()
                
                # 2. Update Payroll Profile
                payroll_profile, _ = PayrollProfile.objects.get_or_create(employee=employee)
                if 'usd_salary' in data: payroll_profile.usd_salary = data['usd_salary']
                if 'zig_salary' in data: payroll_profile.zig_salary = data['zig_salary']
                if 'pay_frequency' in data: payroll_profile.pay_frequency = data['pay_frequency']
                payroll_profile.save()
                
                # 3. Update Bank Account
                bank_account, _ = EmployeeBankAccount.objects.get_or_create(employee=employee, is_primary=True)
                if 'bank_name' in data: bank_account.bank_name = data['bank_name']
                if 'bank_account' in data: bank_account.account_number = data['bank_account']
                bank_account.save()
                
                # 4. Update Statutory Info
                statutory_profile, _ = StatutoryProfile.objects.get_or_create(employee=employee)
                if 'nssa_number' in data: statutory_profile.nssa_number = data['nssa_number']
                if 'zimra_tax_number' in data: statutory_profile.zimra_tax_number = data['zimra_tax_number']
                if 'paye_number' in data: statutory_profile.paye_number = data['paye_number']
                statutory_profile.save()
                
                return EmployeeOrchestrator.get_full_profile(uuid)
                
        except Employees.DoesNotExist:
            return None

# payroll_app/management/commands/seed_payslip_items.py

from django.core.management.base import BaseCommand
from ...models import AllowanceType, DeductionType # Adjust based on your actual app name and model locations

class Command(BaseCommand):
    help = 'Seeds initial AllowanceType and DeductionType data for payslips.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding payslip items...'))

        # --- Allowances ---
        allowances_to_seed = [
            {'name': 'Housing Allowance', 'description': 'Monthly allowance for housing expenses.', 'amount': 500.00},
            {'name': 'Transport Allowance', 'description': 'Allowance for commuting costs.', 'amount': 150.00},
            {'name': 'Performance Bonus', 'description': 'Bonus based on quarterly performance.', 'amount': 300.00},
            {'name': 'Relocation Allowance', 'description': 'One-time allowance for relocation expenses.', 'amount': 1000.00},
            {'name': 'Utilities Allowance', 'description': 'Allowance for utility bills (electricity, water).', 'amount': 80.00},
        ]

        for data in allowances_to_seed:
            obj, created = AllowanceType.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created AllowanceType: {obj.name} (${obj.amount})'))
            else:
                # Optionally update existing ones if values change, but be careful with `get_or_create`
                # For a true "upsert", you might use .update_or_create()
                if obj.description != data['description'] or obj.amount != data['amount']:
                    obj.description = data['description']
                    obj.amount = data['amount']
                    obj.save()
                    self.stdout.write(self.style.WARNING(f'Updated AllowanceType: {obj.name} (${obj.amount})'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'AllowanceType already exists: {obj.name}'))

        # --- Deductions ---
        deductions_to_seed = [
            {'name': 'PAYE (Tax)', 'description': 'Pay As You Earn Income Tax.', 'amount': 0.00}, # Amount can be 0 if calculated dynamically later
            {'name': 'NSSA Contribution', 'description': 'National Social Security Authority contribution.', 'amount': 50.00},
            {'name': 'Medical Aid', 'description': 'Employee contribution to medical aid.', 'amount': 30.00},
            {'name': 'Pension Fund', 'description': 'Employee contribution to pension fund.', 'amount': 75.00},
            {'name': 'Staff Loan Repayment', 'description': 'Deduction for repayment of staff loan.', 'amount': 120.00},
        ]

        for data in deductions_to_seed:
            obj, created = DeductionType.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created DeductionType: {obj.name} (${obj.amount})'))
            else:
                if obj.description != data['description'] or obj.amount != data['amount']:
                    obj.description = data['description']
                    obj.amount = data['amount']
                    obj.save()
                    self.stdout.write(self.style.WARNING(f'Updated DeductionType: {obj.name} (${obj.amount})'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'DeductionType already exists: {obj.name}'))

        self.stdout.write(self.style.SUCCESS('Payslip items seeding complete! ✨'))
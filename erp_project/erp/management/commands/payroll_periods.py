# payroll_app/management/commands/seed_payroll_periods.py
from django.core.management.base import BaseCommand
from ...models import PayrollPeriod

class Command(BaseCommand):
    help = 'Seeds the database with common payroll period types.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Deleting existing Payroll Period Types to avoid duplicates...'))
        PayrollPeriod.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Seeding Payroll Period Types...'))
        periods_data = [
            {'name': 'Monthly', 'frequency_in_days': 30},
            {'name': 'Bi-Weekly', 'frequency_in_days': 14},
            {'name': 'Weekly', 'frequency_in_days': 7},
            {'name': 'Semi-Monthly', 'frequency_in_days': 15},
        ]

        for data in periods_data:
            PayrollPeriod.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(periods_data)} payroll period types.'))

        self.stdout.write(self.style.SUCCESS('Payroll period seeding complete! 📅'))
# payroll_app/management/commands/seed_tax_brackets.py
from django.core.management.base import BaseCommand
from ...models import TaxBracket
from datetime import date

class Command(BaseCommand):
    help = 'Seeds the database with initial Zimbabwe tax bracket data (ZWL/ZiG and USD).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Deleting existing Tax Brackets to avoid duplicates...'))
        TaxBracket.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Seeding ZWL/ZiG Tax Brackets...'))
        zig_brackets_data = [
            {'currency': 'ZWG', 'min_income': 0.00, 'max_income': 1000.00, 'rate': 0.00, 'deduction': 0.00, 'active_from': date(2024, 4, 5)},
            {'currency': 'ZWG', 'min_income': 1000.01, 'max_income': 5000.00, 'rate': 0.20, 'deduction': 200.00, 'active_from': date(2024, 4, 5)},
            {'currency': 'ZWG', 'min_income': 5000.01, 'max_income': 15000.00, 'rate': 0.25, 'deduction': 450.00, 'active_from': date(2024, 4, 5)},
            {'currency': 'ZWG', 'min_income': 15000.01, 'max_income': 30000.00, 'rate': 0.30, 'deduction': 1200.00, 'active_from': date(2024, 4, 5)},
            {'currency': 'ZWG', 'min_income': 30000.01, 'max_income': 50000.00, 'rate': 0.35, 'deduction': 2700.00, 'active_from': date(2024, 4, 5)},
            {'currency': 'ZWG', 'min_income': 50000.01, 'max_income': None, 'rate': 0.40, 'deduction': 5200.00, 'active_from': date(2024, 4, 5)},
        ]

        for data in zig_brackets_data:
            TaxBracket.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(zig_brackets_data)} ZWL/ZiG tax brackets.'))

        self.stdout.write(self.style.SUCCESS('Seeding USD Tax Brackets...'))
        usd_brackets_data = [
            {'currency': 'USD', 'min_income': 0.00, 'max_income': 750.00, 'rate': 0.00, 'deduction': 0.00, 'active_from': date(2024, 1, 1)},
            {'currency': 'USD', 'min_income': 750.01, 'max_income': 2500.00, 'rate': 0.20, 'deduction': 150.00, 'active_from': date(2024, 1, 1)},
            {'currency': 'USD', 'min_income': 2500.01, 'max_income': 5000.00, 'rate': 0.25, 'deduction': 275.00, 'active_from': date(2024, 1, 1)},
            {'currency': 'USD', 'min_income': 5000.01, 'max_income': 10000.00, 'rate': 0.30, 'deduction': 525.00, 'active_from': date(2024, 1, 1)},
            {'currency': 'USD', 'min_income': 10000.01, 'max_income': 15000.00, 'rate': 0.35, 'deduction': 1025.00, 'active_from': date(2024, 1, 1)},
            {'currency': 'USD', 'min_income': 15000.01, 'max_income': None, 'rate': 0.40, 'deduction': 1775.00, 'active_from': date(2024, 1, 1)},
        ]

        for data in usd_brackets_data:
            TaxBracket.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(usd_brackets_data)} USD tax brackets.'))

        self.stdout.write(self.style.SUCCESS('Tax bracket seeding complete! ✨'))
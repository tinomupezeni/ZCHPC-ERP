# human_resources/management/commands/seed_roles.py
from django.core.management.base import BaseCommand
from django.db import transaction
from human_resources.hr_models import Role


class Command(BaseCommand):
    help = 'Seeds the database with all predefined roles'

    @transaction.atomic
    def handle(self, *args, **options):
        roles_data = [
            {"name": "ADMIN", "display_name": "System Administrator", "description": "Full system access"},
            {"name": "HR", "display_name": "Human Resources", "description": "HR department access"},
            {"name": "ACCOUNTANT", "display_name": "Accountant", "description": "Finance and payroll access"},
            {"name": "PROCUREMENT", "display_name": "Procurement Officer", "description": "Procurement department access"},
            {"name": "SALES", "display_name": "Sales Representative", "description": "Sales department access"},
            {"name": "MANAGER", "display_name": "Department Manager", "description": "Management access"},
            {"name": "STAFF", "display_name": "Staff Member", "description": "Basic employee access"},
            {"name": "INTERN", "display_name": "Intern", "description": "Limited intern access"},
        ]

        created_count = 0
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                defaults={
                    "display_name": role_data["display_name"],
                    "description": role_data["description"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role.display_name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {role.display_name}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal roles created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total roles in database: {Role.objects.count()}'))

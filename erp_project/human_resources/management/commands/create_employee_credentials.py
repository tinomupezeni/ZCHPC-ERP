"""
Management command to create user credentials for existing employees.

Usage:
    python manage.py create_employee_credentials

This will:
1. Find all employees without a linked user account
2. Create user accounts with email and surname as password
3. Link the user accounts to the employees
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from human_resources.hr_models import Employees
from authentication.models import CustomUser


class Command(BaseCommand):
    help = 'Create user credentials for existing employees without user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made\n'))

        # Find employees without user accounts
        employees_without_users = Employees.objects.filter(user__isnull=True)
        total = employees_without_users.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('All employees already have user accounts.'))
            return

        self.stdout.write(f'Found {total} employees without user accounts.\n')

        created_count = 0
        linked_count = 0
        skipped_count = 0
        errors = []

        for employee in employees_without_users:
            self.stdout.write(f'\nProcessing: {employee.employee_id} - {employee.first_name} {employee.surname}')

            # Check if employee has email
            if not employee.email:
                self.stdout.write(self.style.WARNING(f'  SKIPPED: No email address'))
                skipped_count += 1
                continue

            # Check if employee has surname (for password)
            if not employee.surname:
                self.stdout.write(self.style.WARNING(f'  SKIPPED: No surname for password'))
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f'  Would create user with email: {employee.email}'))
                self.stdout.write(f'  Password would be: {employee.surname}')
                created_count += 1
                continue

            try:
                with transaction.atomic():
                    # Check if user with this email already exists
                    existing_user = CustomUser.objects.filter(email=employee.email).first()

                    if existing_user:
                        # Link existing user to employee
                        employee.user = existing_user
                        employee.save(update_fields=['user'])
                        self.stdout.write(self.style.SUCCESS(f'  LINKED to existing user: {employee.email}'))
                        linked_count += 1
                    else:
                        # Create new user account
                        user = CustomUser.objects.create_user(
                            email=employee.email,
                            password=employee.surname,
                            first_name=employee.first_name,
                            last_name=employee.surname,
                            is_active=True,
                        )

                        # Link user to employee
                        employee.user = user
                        employee.save(update_fields=['user'])

                        self.stdout.write(self.style.SUCCESS(f'  CREATED user: {employee.email}'))
                        self.stdout.write(f'  EC Number: {employee.employee_id}')
                        self.stdout.write(f'  Password: {employee.surname}')
                        created_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR: {str(e)}'))
                errors.append((employee.employee_id, str(e)))

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'Total employees processed: {total}')
        self.stdout.write(f'User accounts created: {created_count}')
        self.stdout.write(f'Linked to existing users: {linked_count}')
        self.stdout.write(f'Skipped (missing data): {skipped_count}')
        self.stdout.write(f'Errors: {len(errors)}')

        if errors:
            self.stdout.write(self.style.ERROR('\nErrors encountered:'))
            for emp_id, error in errors:
                self.stdout.write(f'  {emp_id}: {error}')

        if not dry_run and created_count > 0:
            self.stdout.write(self.style.WARNING(
                '\nIMPORTANT: Employees should change their passwords after first login!'
            ))
            self.stdout.write('Login credentials:')
            self.stdout.write('  - EC Number: Employee ID (e.g., EMP0001)')
            self.stdout.write('  - Password: Employee surname')

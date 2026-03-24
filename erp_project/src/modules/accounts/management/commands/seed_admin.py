"""
Management command to seed admin superuser with IT department employee profile.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates admin superuser for ZCHPC ERP with IT department employee profile'

    def handle(self, *args, **options):
        email = 'admin@zchpc.com'
        password = 'admin'

        # Check if admin already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user with email {email} already exists!')
            )
            return

        with transaction.atomic():
            # Import HR models
            from modules.hr.infrastructure.persistence.models import (
                Department, Role, Position, Employees
            )

            # Create or get IT department
            it_department, dept_created = Department.objects.get_or_create(
                name='IT',
                defaults={'description': 'Information Technology Department'}
            )
            if dept_created:
                self.stdout.write(self.style.SUCCESS('Created IT department'))

            # Create or get ADMIN role
            admin_role, role_created = Role.objects.get_or_create(
                name='ADMIN',
                defaults={
                    'display_name': 'System Administrator',
                    'description': 'Full system access',
                    'permissions': ['*'],  # All permissions
                }
            )
            if role_created:
                self.stdout.write(self.style.SUCCESS('Created ADMIN role'))

            # Create or get IT Manager position
            it_position, pos_created = Position.objects.get_or_create(
                title='IT Manager',
                defaults={'department': it_department, 'description': 'IT Department Manager'}
            )
            if pos_created:
                self.stdout.write(self.style.SUCCESS('Created IT Manager position'))

            # Create superuser
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator',
                is_staff=True,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {email}'))

            # Create employee profile linked to the user
            employee = Employees.objects.create(
                user=user,
                first_name='System',
                surname='Administrator',
                email=email,
                department=it_department,
                position=it_position,
                role=admin_role,
                employee_type='Full-time',
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created employee profile: {employee.employee_id}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'Admin superuser created successfully!\n'
                f'{"="*60}\n'
                f'Email:       {email}\n'
                f'Password:    {password}\n'
                f'Department:  IT\n'
                f'Position:    IT Manager\n'
                f'Role:        ADMIN\n'
                f'Employee ID: {employee.employee_id}\n'
                f'{"="*60}\n'
                f'WARNING: Change this password in production!\n'
                f'{"="*60}\n'
            )
        )

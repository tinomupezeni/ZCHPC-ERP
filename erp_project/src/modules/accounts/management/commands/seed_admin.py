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
        email = 'admin@zchpc.ac.zw'
        password = 'admin'

        # Import HR models within the handle method to avoid AppRegistryNotReady error
        from modules.hr.infrastructure.persistence.models import (
            Department, Role, Position, Employees
        )
        from django.contrib.auth import get_user_model
        User = get_user_model() # Ensure CustomUser is properly loaded

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
                'permissions': ['*'],
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

        user = None
        employee = None # Initialize employee to None

        user_exists = User.objects.filter(email=email).exists()

        if user_exists:
            user = User.objects.get(email=email)
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated existing user {email} to be a superuser and staff.'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user with email {email} already exists and is a superuser/staff.'))
        else:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    email=email,
                    password=password,
                    first_name='System',
                    last_name='Administrator',
                    is_staff=True,
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Created superuser: {email}'))

        # Now, create or update the employee profile for the user
        if user:
            employee, employee_created = Employees.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': user.first_name,
                    'surname': user.last_name,
                    'email': user.email,
                    'department': it_department,
                    'position': it_position,
                    'role': admin_role,
                    'employee_type': 'Full-time',
                    'is_active': True,
                }
            )
            if not employee_created:
                # If employee profile already exists, ensure its role is ADMIN
                if employee.role != admin_role:
                    employee.role = admin_role
                    employee.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated existing employee profile for {email} with ADMIN role.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Employee profile for {email} already exists with ADMIN role.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Created employee profile: {employee.employee_id}'))

        self.stdout.write(
            self.style.SUCCESS(f"""
{"="*60}
Admin superuser and employee profile created/updated successfully!
{"="*60}
Email:       {email}
Password:    {password}
Department:  IT
Position:    IT Manager
Role:        ADMIN
{f'Employee ID: {employee.employee_id}' if employee else ''}
{"="*60}
WARNING: Change this password in production!
{"="*60}
""")
        )
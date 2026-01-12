from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from human_resources.hr_models import Department, Employees, Role # Ensure correct import path

class Command(BaseCommand):
    help = 'Seeds the database with an initial admin user and their employee profile.'

    @transaction.atomic
    def handle(self, *args, **options):
        CustomUser = get_user_model()
        
        # 1. Ensure the "System" department exists
        system_department, created = Department.objects.get_or_create(name='System')

        # 2. Get OR CREATE the ADMIN Role object
        # This fixes the "Role not found" error if the signal didn't run
        admin_role, created = Role.objects.get_or_create(
            name='ADMIN',
            defaults={'display_name': 'System Administrator'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created "ADMIN" role.'))

        # 3. Check if an admin user already exists
        if not CustomUser.objects.filter(email='admin@zchpc.com').exists():
            self.stdout.write(self.style.WARNING('Creating admin user...'))
            
            admin_user = CustomUser.objects.create_superuser(
                email='admin@zchpc.com',
                password='admin',
                first_name='Admin',
                last_name='User'
            )

            Employees.objects.create(
                user=admin_user,
                first_name='Admin',
                surname='User',
                email='admin@zchpc.com',
                role=admin_role,
                department=system_department,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully seeded Admin.'))
        else:
            self.stdout.write(self.style.WARNING('Admin already exists.'))
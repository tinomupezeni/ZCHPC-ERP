# authentication/management/commands/seed_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction  # <-- 1. Import transaction
from human_resources.hr_models import Department, Employees  # <-- 2. Import Employees

class Command(BaseCommand):
    help = 'Seeds the database with an initial admin user and their employee profile.'

    @transaction.atomic  # 3. Wrap the handle in a transaction
    def handle(self, *args, **options):
        CustomUser = get_user_model()
        
        # Ensure the "System" department exists
        system_department, created = Department.objects.get_or_create(name='System')
        if created:
            self.stdout.write(self.style.SUCCESS('Created "System" department.'))

        # Check if an admin user already exists
        if not CustomUser.objects.filter(email='admin@zchpc.com').exists():
            
            # --- 4. Create the CustomUser (Auth record) ---
            # Only pass fields that exist on the CustomUser model
            self.stdout.write(self.style.WARNING('Creating admin user...'))
            admin_user = CustomUser.objects.create_superuser(
                email='admin@zchpc.com',
                password='admin',
                first_name='Admin', # Corrected: first_name
                last_name='User'   # Corrected: last_name
                # 'is_active' is set to True by create_superuser
            )

            # --- 5. Create the Employees (HR record) ---
            # Pass all the HR-related fields here
            Employees.objects.create(
                user=admin_user,  # Link to the user we just created
                role='ADMIN',     # Match ROLE_CHOICES
                department=system_department,
                is_active=True
                # The Employees.save() method will auto-generate the employee_id
            )
            
            self.stdout.write(self.style.SUCCESS('Successfully created admin user and employee profile.'))

            # Optional: Add user to a default 'Admin' group
            try:
                admin_group, created = Group.objects.get_or_create(name='Admin')
                admin_user.groups.add(admin_group)
                self.stdout.write(self.style.SUCCESS('Successfully added admin user to "Admin" group.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not add user to group: {e}'))

        else:
            self.stdout.write(self.style.WARNING('Admin user "admin@zchpc.com" already exists. No action taken.'))
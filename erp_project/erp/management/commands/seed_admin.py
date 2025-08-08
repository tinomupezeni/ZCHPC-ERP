# your_app_name/management/commands/seed_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Seeds the database with an initial admin user.'

    def handle(self, *args, **options):
        CustomUser = get_user_model()
        
        # Check if an admin user already exists to prevent duplicates
        if not CustomUser.objects.filter(email='admin@zchpc.com').exists():
            admin_user = CustomUser.objects.create_superuser(
                username='admin_username',  # AbstractUser still has a username field
                email='admin@zchpc.com',
                password='admin',  # In a production environment, use environment variables for this
                firstname='Admin',
                surname='User',
                role='admin',
                department='System',
                isActive=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user: admin@zchpc.com'))

            # Optional: Add user to a default 'Admin' group if it exists
            try:
                admin_group, created = Group.objects.get_or_create(name='Admin')
                admin_user.groups.add(admin_group)
                self.stdout.write(self.style.SUCCESS('Successfully added admin user to "Admin" group.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not add user to group: {e}'))

        else:
            self.stdout.write(self.style.WARNING('Admin user already exists. No action taken.'))
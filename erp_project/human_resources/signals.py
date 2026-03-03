from django.db.models.signals import post_save
from django.dispatch import receiver


def create_default_roles(sender, **kwargs):
    """
    Automatically populates the Role table with standard ERP roles
    after the database migration finishes.
    """
    from .hr_models import Role  # Lazy import

    DEFAULT_ROLES = [
        {'name': 'ADMIN', 'display_name': 'System Administrator'},
        {'name': 'HR', 'display_name': 'Human Resources Manager'},
        {'name': 'ACCOUNTANT', 'display_name': 'Accountant'},
        {'name': 'PROCUREMENT', 'display_name': 'Procurement Officer'},
        {'name': 'SALES', 'display_name': 'Sales Representative'},
        {'name': 'MANAGER', 'display_name': 'Department Manager'},
        {'name': 'STAFF', 'display_name': 'Regular Staff'},
    ]

    for role_data in DEFAULT_ROLES:
        Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'display_name': role_data['display_name']}
        )


@receiver(post_save, sender='human_resources.Employees')
def create_employee_user_account(sender, instance, created, **kwargs):
    """
    Automatically creates a user account when an employee is added.

    Credentials:
    - Login: EC number (employee_id, e.g., EMP0001)
    - Password: Employee's surname (case-sensitive)

    The user can change their password after first login.
    """
    from authentication.models import CustomUser

    # Only create user for new employees without an existing user account
    if created and not instance.user and instance.email:
        try:
            # Check if user with this email already exists
            existing_user = CustomUser.objects.filter(email=instance.email).first()

            if existing_user:
                # Link existing user to employee
                instance.user = existing_user
                # Use update to avoid triggering the signal again
                sender.objects.filter(pk=instance.pk).update(user=existing_user)
            else:
                # Create new user account
                # Password is set to the employee's surname
                password = instance.surname

                user = CustomUser.objects.create_user(
                    email=instance.email,
                    password=password,
                    first_name=instance.first_name,
                    last_name=instance.surname,
                    is_active=True,
                )

                # Link user to employee
                # Use update to avoid triggering the signal again
                sender.objects.filter(pk=instance.pk).update(user=user)

        except Exception as e:
            # Log the error but don't prevent employee creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create user account for employee {instance.employee_id}: {str(e)}")
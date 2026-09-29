"""
Django signals for the HR module.

Handles automatic user account creation when employees are added.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def create_default_roles(sender, **kwargs):
    """Populate the Role table with standard ERP roles."""
    from .infrastructure.persistence.models import Role

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


@receiver(post_save, sender='hr.Employees')
def create_employee_user_account(sender, instance, created, **kwargs):
    """
    Automatically creates a user account when an employee is added.

    Login: email (/api/v2/auth/token/) or EC number (/api/v2/portal/auth/login/).
    Password (REM-07): a random temporary password from the identity module's
    generator - never derived from employee data. The account is marked
    must_change_password, so it can do nothing but change that password.

    The plaintext is handed back once on ``instance.temporary_password`` so
    the service creating the employee can return it to its authorized
    creator; it is never stored or logged.
    """
    from modules.identity.application.services import generate_temp_password
    from modules.identity.infrastructure.persistence.models import CustomUser

    if created and not instance.user and instance.email:
        try:
            existing_user = CustomUser.objects.filter(email=instance.email).first()

            if existing_user:
                sender.objects.filter(pk=instance.pk).update(user=existing_user)
            else:
                temporary_password = generate_temp_password()
                user = CustomUser.objects.create_user(
                    email=instance.email,
                    password=temporary_password,
                    first_name=instance.first_name,
                    last_name=instance.surname,
                    is_active=True,
                    must_change_password=True,
                )
                sender.objects.filter(pk=instance.pk).update(user=user)
                instance.temporary_password = temporary_password
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create user for employee {instance.employee_id}: {e}")

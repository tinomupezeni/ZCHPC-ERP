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
    Login: EC number (employee_id)
    Password: Employee's surname
    """
    from modules.identity.infrastructure.persistence.models import CustomUser

    if created and not instance.user and instance.email:
        try:
            existing_user = CustomUser.objects.filter(email=instance.email).first()

            if existing_user:
                sender.objects.filter(pk=instance.pk).update(user=existing_user)
            else:
                password = instance.surname
                user = CustomUser.objects.create_user(
                    email=instance.email,
                    password=password,
                    first_name=instance.first_name,
                    last_name=instance.surname,
                    is_active=True,
                )
                sender.objects.filter(pk=instance.pk).update(user=user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create user for employee {instance.employee_id}: {e}")

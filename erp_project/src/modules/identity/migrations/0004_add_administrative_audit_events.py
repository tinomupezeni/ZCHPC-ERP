# Generated migration for administrative audit events

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('identity', '0003_seed_core_system_modules'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='event_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    # Authentication events
                    ('SUCCESS', 'Login Success'),
                    ('FAILED', 'Login Failed'),
                    ('LOCKOUT', 'Account Locked'),
                    ('FORCE_RESET', 'Forced Password Reset'),
                    ('LOGOUT', 'Logout'),
                    # Administrative events
                    ('USER_CREATED', 'User Created'),
                    ('USER_DELETED', 'User Deleted'),
                    ('USER_UPDATED', 'User Updated'),
                    ('ROLE_ASSIGNED', 'Role Assigned'),
                    ('ROLE_REMOVED', 'Role Removed'),
                    ('PERMISSION_GRANTED', 'Permission Granted'),
                    ('PERMISSION_REVOKED', 'Permission Revoked'),
                    ('EMPLOYEE_CREATED', 'Employee Created'),
                    ('EMPLOYEE_UPDATED', 'Employee Updated'),
                    ('EMPLOYEE_DELETED', 'Employee Deleted'),
                ]
            ),
        ),
    ]

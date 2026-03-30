# Generated manually for employee_id format change

import uuid
from django.db import migrations, models


def convert_uuid_to_emp_format(apps, schema_editor):
    """Convert existing UUID employee_ids to EMP0001 format."""
    Employee = apps.get_model('hr', 'Employees')
    db_alias = schema_editor.connection.alias

    employees = Employee.objects.using(db_alias).order_by('id').all()
    for idx, employee in enumerate(employees, start=1):
        # Generate new EMP format employee_id
        employee.employee_id = f"EMP{idx:04d}"
        employee.save()


def reverse_conversion(apps, schema_editor):
    """Reverse: we can't perfectly reverse, but we keep the uuid."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0007_add_pension_emergency_fields"),
    ]

    operations = [
        # Step 1: Rename employee_id (UUID) to uuid
        migrations.RenameField(
            model_name='employees',
            old_name='employee_id',
            new_name='uuid',
        ),

        # Step 2: Add new employee_id CharField (without unique constraint initially)
        migrations.AddField(
            model_name='employees',
            name='employee_id',
            field=models.CharField(max_length=20, blank=True, default=''),
        ),

        # Step 3: Convert data - generate EMP0001 format IDs
        migrations.RunPython(convert_uuid_to_emp_format, reverse_conversion),

        # Step 4: Now add unique constraint
        migrations.AlterField(
            model_name='employees',
            name='employee_id',
            field=models.CharField(max_length=20, unique=True, blank=True),
        ),
    ]

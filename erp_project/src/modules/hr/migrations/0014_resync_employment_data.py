"""
Re-copy Employees' inline employment/emergency-contact fields into the
normalized EmploymentDetails/EmergencyContact tables. Migration 0012 did this
once, but application code kept writing to the inline columns afterwards, so
this catches any drift before the inline columns are dropped (0016).
"""
from django.db import migrations


def resync_employment_data(apps, schema_editor):
    Employees = apps.get_model('hr', 'Employees')
    EmploymentDetails = apps.get_model('hr', 'EmploymentDetails')
    EmergencyContact = apps.get_model('hr', 'EmergencyContact')

    for employee in Employees.objects.all():
        EmploymentDetails.objects.update_or_create(
            employee=employee,
            defaults={
                'department_id': employee.department_id,
                'position_id': employee.position_id,
                'reports_to_id': employee.reports_to_id,
                'date_joined': employee.date_joined,
                'contract_from': employee.contract_from,
                'contract_to': employee.contract_to,
                'employee_type': employee.employee_type,
            },
        )

        has_emergency_data = any([
            employee.emergency_contact_name,
            employee.emergency_contact_number,
            employee.emergency_contact_relationship,
        ])
        if has_emergency_data:
            existing = EmergencyContact.objects.filter(employee=employee).first()
            if existing:
                existing.name = employee.emergency_contact_name or ''
                existing.relationship = employee.emergency_contact_relationship or ''
                existing.phone = employee.emergency_contact_number or ''
                existing.save()
            else:
                EmergencyContact.objects.create(
                    employee=employee,
                    name=employee.emergency_contact_name or '',
                    relationship=employee.emergency_contact_relationship or '',
                    phone=employee.emergency_contact_number or '',
                )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0013_remove_employees_bank_account_and_more'),
    ]

    operations = [
        migrations.RunPython(resync_employment_data, noop_reverse),
    ]

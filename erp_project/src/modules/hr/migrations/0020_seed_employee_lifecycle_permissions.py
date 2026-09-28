"""
Top up hr.employee.create and hr.employee.deactivate (REM-01).

Creating and deactivating employees now require their own capabilities
(modules.hr.application.authorization.permissions.EmployeeManagementPermissions).
Before REM-01 neither was checked at all, so no role was ever *deliberately*
granted them and there is no prior access to reproduce.

Which roles receive them
------------------------
No role is chosen by name - which job title administers employees is the
organisation's decision, made through the Roles API. The only data-driven
signal the store already holds is the explicit employee-administration grant
``hr.employee.manage_assignments``: a role carrying that exact string was
deliberately made an employee administrator. Those roles get the two new
strings; every other role is left untouched.

Roles holding ``*``, ``hr.*`` or ``hr.employee.*`` already satisfy the new
checks through Permission.matches() and need nothing added. Any other role
(including the seeded HUMAN_RESOURCES role, which holds only hr.role.manage)
must be granted the capabilities through the Roles API to create or
deactivate employees.

Idempotent and additive, like 0018/0019: only missing strings are appended,
nothing else on a role is changed. The reverse removes exactly these two
strings from the roles this migration would target, and nothing else - it
cannot tell its own grant from an administrator's identical one, the same
limitation 0018/0019 accept.
"""

from django.db import migrations

# Snapshot of the capability strings at the time of this migration, copied
# rather than imported so later edits cannot change history.
TRIGGER_PERMISSION = "hr.employee.manage_assignments"
GRANTED_PERMISSIONS = ["hr.employee.create", "hr.employee.deactivate"]


def _targets(Role):
    for role in Role.objects.all():
        if TRIGGER_PERMISSION in list(role.permissions or []):
            yield role


def grant(apps, schema_editor):
    Role = apps.get_model("hr", "Role")
    for role in _targets(Role):
        current = list(role.permissions or [])
        additions = [p for p in GRANTED_PERMISSIONS if p not in current]
        if additions:
            role.permissions = current + additions
            role.save(update_fields=["permissions"])


def revoke(apps, schema_editor):
    Role = apps.get_model("hr", "Role")
    for role in _targets(Role):
        current = list(role.permissions or [])
        remaining = [p for p in current if p not in GRANTED_PERMISSIONS]
        if remaining != current:
            role.permissions = remaining
            role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0019_seed_hr_role"),
    ]

    operations = [
        migrations.RunPython(grant, revoke),
    ]

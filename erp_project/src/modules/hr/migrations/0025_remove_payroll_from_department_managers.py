"""
Remove ``payroll.*`` from the department-manager roles (INT-01 Q1).

The supervisor decided (Fri 2026-10-09) that department heads see no payroll.
Migration 0017 copied the legacy middleware map onto empty roles, and that map
gave MANAGER and DEPARTMENT_MANAGER ``payroll.*`` - so the grant sits in live
role rows, not only in a seed.

Forward removes exactly the string ``payroll.*`` from roles whose name
normalises (as 0017 did) to MANAGER or DEPARTMENT_MANAGER, and changes nothing
else on them. A narrower payroll grant, or ``*``, is not touched: neither came
from 0017, so either one was an administrator's deliberate choice.

Reverse adds ``payroll.*`` back to those roles where it is missing. Like
0018-0020, it cannot tell a role this migration changed from one that never
held the grant (accepted, owner decision 2026-10-11).
"""

from django.db import migrations

# Copied rather than imported so later edits cannot change history.
ROLE_NAMES = {"MANAGER", "DEPARTMENT_MANAGER"}
REMOVED_PERMISSION = "payroll.*"


def normalise(name: str) -> str:
    """The role-name normalisation 0017 applied."""
    return (name or "").upper().replace(" ", "_").replace("-", "_")


def _targets(Role):
    for role in Role.objects.all():
        if normalise(role.name) in ROLE_NAMES:
            yield role


def remove_payroll(apps, schema_editor):
    Role = apps.get_model("hr", "Role")
    for role in _targets(Role):
        current = list(role.permissions or [])
        remaining = [p for p in current if p != REMOVED_PERMISSION]
        if remaining != current:
            role.permissions = remaining
            role.save(update_fields=["permissions"])


def restore_payroll(apps, schema_editor):
    Role = apps.get_model("hr", "Role")
    for role in _targets(Role):
        current = list(role.permissions or [])
        if REMOVED_PERMISSION not in current:
            role.permissions = current + [REMOVED_PERMISSION]
            role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0024_employee_lifecycle_event"),
    ]

    operations = [
        migrations.RunPython(remove_payroll, restore_payroll),
    ]

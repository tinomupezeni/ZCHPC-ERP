"""
Create the HUMAN_RESOURCES role, and ensure it holds the new
role-administration capability (REM-05).

Why HUMAN_RESOURCES, not HR
----------------------------
Both names appear as synonyms in the now-deprecated legacy permission maps
(modules.identity.infrastructure.permissions.ROLE_PERMISSIONS,
modules.identity.domain.entities.role.DEFAULT_ROLE_PERMISSIONS), but only
HUMAN_RESOURCES has a live consumer anywhere in the system:
employee-portal/src/hooks/useRole.ts's RoleName union recognises
'HUMAN_RESOURCES' (not 'HR') as the name mapping to its 'hr' roleGroup.
This migration uses the one name that already has a real, current
consumer, rather than reintroducing a second alias no live code expects.

Why hr.role.manage only - not the dormant legacy HR bundle
------------------------------------------------------------
The confirmed business decision for REM-05 is that role/permission
administration belongs to a dedicated HR role, decided independently of
the old, unused HR permission bundle
(hr.*, attendance.*, leave.*, recruitment.*, payroll.*, identity.*,
portal.*) that this repository already establishes has no runtime
consumer (see identity/infrastructure/permissions.py's own docstring, and
AUD-01 R3). Granting that bundle here would silently re-introduce exactly
the "hr.* implies everything, including administering authorization
itself" conflation REM-05 exists to remove - and since Permission.matches()
treats an app-level wildcard as matching any capability under that prefix
(by design, unchanged here), hr.* would imply hr.role.manage too. This
migration only ever adds the single hr.role.manage string, never a
wildcard, and never touches any other permission already on the role.

Deterministic regardless of prior state (REM-05 review fix)
--------------------------------------------------------------
The first version of this migration skipped every field, including the
permission grant, whenever a role named HUMAN_RESOURCES already existed -
reasoned as "never overwrite an administrator's own configuration". That
reasoning was wrong for this specific field: migration 0017
(hr/migrations/0017_seed_role_permissions.py) still contains a dormant
legacy grant for a role named HUMAN_RESOURCES (among others) with empty
permissions, and would hand it the old hr.* bundle if such a role existed
with no permissions at the moment 0017 executed - a scenario 0017's own
guard cannot distinguish from any other "administrator's own
configuration". If that ever happened before this migration ran, the old
"skip entirely" logic would leave the resulting hr.* grant in place
untouched, silently defeating this migration's own stated goal above.

So the forward function below always ensures hr.role.manage specifically
is present - whether the role is newly created or already existed, and
regardless of whatever else is already on it - without ever removing or
overwriting anything else already configured. This mirrors
0018_seed_purchase_request_permissions's additive, string-level merge
(never "skip if any permissions exist", always "top up exactly the
strings this migration is responsible for"), rather than 0017's
whole-role "skip if configured" guard. It does not strip any hr.*
permission a role might already hold from another source; removing an
already-granted wildcard is a separate policy decision, out of scope here.

Idempotent: running this forward function again, in any state, converges
to the same result - HUMAN_RESOURCES exists and includes hr.role.manage,
nothing else changed.
"""

from django.db import migrations

ROLE_NAME = "HUMAN_RESOURCES"
MANAGED_PERMISSION = "hr.role.manage"


def seed_hr_role(apps, schema_editor):
    """Ensure HUMAN_RESOURCES exists and holds hr.role.manage, however it got here."""
    Role = apps.get_model("hr", "Role")

    role, created = Role.objects.get_or_create(
        name=ROLE_NAME,
        defaults={
            "display_name": "Human Resources",
            "description": "Administers ERP roles and permissions.",
            "permissions": [MANAGED_PERMISSION],
        },
    )
    if created:
        return  # defaults above already granted exactly what this migration owns

    current = list(role.permissions or [])
    if MANAGED_PERMISSION in current:
        return  # already present (possibly via an hr.* grant - see module docstring) - nothing to add

    role.permissions = current + [MANAGED_PERMISSION]
    role.save(update_fields=["permissions"])


def unseed_hr_role(apps, schema_editor):
    """
    Remove exactly the hr.role.manage string this migration is responsible
    for, from the HUMAN_RESOURCES role, leaving every other permission and
    the role itself untouched - the same narrow, string-level reverse
    0018_seed_purchase_request_permissions uses, and for the same reason:
    this migration cannot tell its own grant apart from one an
    administrator made independently, so it removes only the specific
    string it owns, never the role, and never anything else on it.
    """
    Role = apps.get_model("hr", "Role")

    try:
        role = Role.objects.get(name=ROLE_NAME)
    except Role.DoesNotExist:
        return

    current = list(role.permissions or [])
    if MANAGED_PERMISSION not in current:
        return

    role.permissions = [p for p in current if p != MANAGED_PERMISSION]
    role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0018_seed_purchase_request_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_hr_role, unseed_hr_role),
    ]

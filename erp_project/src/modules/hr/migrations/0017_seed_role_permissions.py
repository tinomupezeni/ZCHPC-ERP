"""
Move the legacy middleware role map into the authoritative permission store.

RBACMiddleware used to authorize route access from a hard-coded
``ROLE_PERMISSIONS`` map keyed by role name, entirely separate from
``hr.Role.permissions``. The middleware now reads ``hr.Role.permissions``, so
any role that has no permissions recorded would lose the access the legacy map
used to grant it.

This migration copies the legacy grants onto roles that have none, reproducing
each role's existing access exactly. Roles whose permissions have already been
configured are left untouched, and role names absent from the legacy map are
left empty - they were denied by the old map too.
"""

from django.db import migrations

# Snapshot of modules.identity.infrastructure.permissions.ROLE_PERMISSIONS at
# the time of this migration. Copied rather than imported so that re-running
# history cannot be changed by later edits to that module.
_HR_PERMISSIONS = [
    "hr.*",
    "attendance.*",
    "leave.*",
    "recruitment.*",
    "payroll.*",
    "identity.*",
    "portal.*",
]

LEGACY_ROLE_PERMISSIONS = {
    "ADMIN": ["*"],
    "SYSTEM_ADMINISTRATOR": ["*"],
    "HR": list(_HR_PERMISSIONS),
    "HUMAN_RESOURCES": list(_HR_PERMISSIONS),
    "ACCOUNTANT": ["payroll.*", "accounts.*", "identity.*", "portal.*"],
    "PROCUREMENT": ["procurement.*", "identity.*", "portal.*"],
    "PROCUREMENT_OFFICER": ["procurement.*", "identity.*", "portal.*"],
    "SALES": ["sales.*", "identity.*", "portal.*"],
    "SALES_REPRESENTATIVE": ["sales.*", "identity.*", "portal.*"],
    "MANAGER": [
        "hr.*",
        "attendance.*",
        "leave.*",
        "payroll.*",
        "reports.*",
        "identity.*",
        "portal.*",
    ],
    "DEPARTMENT_MANAGER": [
        "hr.*",
        "attendance.*",
        "leave.*",
        "payroll.*",
        "reports.*",
        "identity.*",
        "portal.*",
    ],
    "STAFF": ["identity.*", "self.*", "portal.*"],
    "REGULAR_STAFF": ["identity.*", "self.*", "portal.*"],
    "INTERN": ["identity.*", "self.*", "portal.*"],
}


def normalise(name: str) -> str:
    """Match the role-name normalisation the legacy middleware applied."""
    return (name or "").upper().replace(" ", "_").replace("-", "_")


def seed_role_permissions(apps, schema_editor):
    """Give un-configured roles the access the legacy map used to grant them."""
    Role = apps.get_model("hr", "Role")

    for role in Role.objects.all():
        if role.permissions:
            continue  # already configured - never overwrite an admin's choice

        legacy = LEGACY_ROLE_PERMISSIONS.get(normalise(role.name))
        if not legacy:
            continue  # unknown to the legacy map, which denied it too

        role.permissions = list(legacy)
        role.save(update_fields=["permissions"])


def unseed(apps, schema_editor):
    """
    Reverse is intentionally a no-op.

    Permissions may have been edited after seeding, so removing them again
    could destroy real configuration.
    """


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0016_department_head"),
    ]

    operations = [
        migrations.RunPython(seed_role_permissions, unseed),
    ]

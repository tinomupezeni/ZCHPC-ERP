"""
Grant the redesigned Purchase Request capabilities to the roles that need
them (Slice F09-PR).

modules.procurement.application.authorization.permissions defines
DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS as a *reference* mapping - nothing
applies it. hr.Role rows created with no permissions (the JSONField default)
or through the HR Roles API therefore hold no procurement.purchase_request.*
capability at all, so RBACMiddleware's coarse route gate
(modules.identity.infrastructure.middleware.RBACMiddleware) 403s every real
employee, department manager and accountant before any Purchase Request view
is ever reached. This migration is what actually grants the capability.

Snapshot, not import
---------------------
The permission list below is copied from
modules.procurement.application.authorization.permissions as of this
migration's authoring, restricted to the six roles this slice targets
(REGULAR_STAFF, INTERN, DEPARTMENT_MANAGER, ACCOUNTANT, PROCUREMENT_OFFICER,
HUMAN_RESOURCES). SALES_REPRESENTATIVE is present in that module's mapping but
deliberately excluded here - it is outside this slice's target role list.
GENERAL_MANAGER/DIRECTOR grants are absent from the source mapping itself,
because no such roles exist in the current role vocabulary.

Copied rather than imported for the same reason 0017_seed_role_permissions
copies LEGACY_ROLE_PERMISSIONS instead of importing it: a later edit to the
application module must not silently change what this migration did when it
was applied to a real database. Migration history has to stay reproducible
independently of the application code's current state.

Matching, additive merge
-------------------------
Roles are matched by name using the exact normalisation
0017_seed_role_permissions.normalise already applies (case/space/hyphen
insensitive), copied here rather than imported for the same reason as above.
A role whose normalised name is not one of the six targets is left
untouched - this migration never invents a role.

This migration's merge is a true union, not "fill only if empty":

    role.permissions = existing_permissions + (granted permissions not
                        already present)

That is a deliberate difference from 0017, which skips any role that already
has *any* permissions recorded at all (0017's job was "restore exactly what a
role held under the legacy map"; this migration's job is "add a capability a
role does not yet have", regardless of what else that role already holds).
Nothing existing is ever removed or reordered, and a permission the role
already had - from 0017, from an administrator, or from a previous run of
this migration - is never duplicated.

Known limitation, and why this migration ships a real reverse anyway
-----------------------------------------------------------------------
0017's reverse is intentionally a no-op: it restores potentially many
permissions across many roles, and it cannot tell a permission it granted
apart from one an administrator granted independently later, so removing them
again risks destroying real configuration.

This migration's grant is much narrower (eleven fixed capability strings,
across six specific roles, all under the procurement.purchase_request.*
vocabulary this migration alone introduces to any of these roles), so the
same ambiguity is judged an acceptable, narrow, documented risk rather than a
reason to refuse a reverse outright: reversing removes exactly the
granted strings that are still present on a matched role's permission list.
The one edge case this cannot distinguish is an administrator manually
granting one of these same eleven strings independently before or after this
migration runs - reversing would remove that grant too, indistinguishable
from what this migration added. Given how narrow and purpose-specific this
permission set is, that risk is accepted rather than declining to reverse.
"""

from django.db import migrations


def normalise(name: str) -> str:
    """Match the role-name normalisation 0017_seed_role_permissions applies."""
    return (name or "").upper().replace(" ", "_").replace("-", "_")


# Snapshot of modules.procurement.application.authorization.permissions
# .DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS at the time of this migration,
# restricted to this slice's six target roles. See the module docstring for
# why this is copied rather than imported.
_REQUESTER_PERMISSIONS = [
    "procurement.purchase_request.create",
    "procurement.purchase_request.view",
    "procurement.purchase_request.submit",
    "procurement.purchase_request.correct",
    "procurement.purchase_request.resubmit",
]

PURCHASE_REQUEST_ROLE_PERMISSIONS = {
    "REGULAR_STAFF": list(_REQUESTER_PERMISSIONS),
    "INTERN": list(_REQUESTER_PERMISSIONS),
    "DEPARTMENT_MANAGER": [
        *_REQUESTER_PERMISSIONS,
        "procurement.purchase_request.department_head_approve",
        "procurement.purchase_request.reject",
    ],
    "ACCOUNTANT": [
        *_REQUESTER_PERMISSIONS,
        "procurement.purchase_request.accounts_verify",
        "procurement.purchase_request.reject",
    ],
    "PROCUREMENT_OFFICER": [
        *_REQUESTER_PERMISSIONS,
        "procurement.purchase_request.process",
    ],
    "HUMAN_RESOURCES": list(_REQUESTER_PERMISSIONS),
}


def grant_purchase_request_permissions(apps, schema_editor):
    """Add each matched role's Purchase Request grant to whatever it already holds."""
    Role = apps.get_model("hr", "Role")

    for role in Role.objects.all():
        grant = PURCHASE_REQUEST_ROLE_PERMISSIONS.get(normalise(role.name))
        if not grant:
            continue  # not one of this slice's six target roles

        current = list(role.permissions or [])
        additions = [permission for permission in grant if permission not in current]
        if not additions:
            continue  # already fully granted - idempotent no-op

        role.permissions = current + additions
        role.save(update_fields=["permissions"])


def revoke_purchase_request_permissions(apps, schema_editor):
    """
    Remove exactly the granted strings this migration would add, from each
    matched role, leaving every other permission untouched.

    See the module docstring for the narrow, accepted ambiguity this carries.
    """
    Role = apps.get_model("hr", "Role")

    for role in Role.objects.all():
        grant = PURCHASE_REQUEST_ROLE_PERMISSIONS.get(normalise(role.name))
        if not grant:
            continue

        current = list(role.permissions or [])
        remaining = [permission for permission in current if permission not in grant]
        if remaining == current:
            continue  # role never had any of these - nothing to undo

        role.permissions = remaining
        role.save(update_fields=["permissions"])


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0017_seed_role_permissions"),
    ]

    operations = [
        migrations.RunPython(
            grant_purchase_request_permissions,
            revoke_purchase_request_permissions,
        ),
    ]

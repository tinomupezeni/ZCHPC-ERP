"""
Coarse route access, derived from the authoritative permission model.

``hr.Role.permissions`` is the single source of truth for what a role may do.
It is administered through the HR roles API, loaded into the identity domain by
``DjangoRoleRepository``, and consumed by per-module authorization such as the
procurement Purchase Request policy.

This module answers only the coarse question the HTTP gate is responsible for:

    may this authenticated user reach this route family at all?

It deliberately does not answer which operation the user may perform, or on
which record - those belong to each module's own authorization layer.

Route families are identified by the URL application namespace, normalised onto
the module vocabulary that permissions already use (``procurement_v2`` ->
``procurement``), so a role granted any ``procurement.*`` capability - including
a narrow one such as ``procurement.purchase_request.submit`` - can reach the
procurement routes and be judged there.
"""

from modules.identity.domain.value_objects import PermissionSet

# URL application namespaces carry a version suffix that the permission
# vocabulary does not (accounts_v2 -> accounts).
_APP_NAME_SUFFIXES = ("_v2",)


def module_for_app(app_name: str) -> str:
    """
    Normalise a URL application namespace onto its permission module name.

    >>> module_for_app("procurement_v2")
    'procurement'
    >>> module_for_app("hr")
    'hr'
    """
    module = (app_name or "").strip().lower()
    for suffix in _APP_NAME_SUFFIXES:
        if module.endswith(suffix):
            return module[: -len(suffix)]
    return module


def permission_set_for_user(user) -> PermissionSet | None:
    """
    The permissions granted to this user by their employee role.

    Returns None when no role can be established, which callers must treat as
    a denial rather than as an empty-but-valid permission set.
    """
    # Reverse one-to-one: Django raises an AttributeError subclass when absent.
    employee = getattr(user, "employee_profile", None)
    if employee is None:
        return None

    role = getattr(employee, "role", None)
    if role is None:
        return None

    return PermissionSet.from_list(list(role.permissions or []))


def grants_module_access(permissions: PermissionSet, module: str) -> bool:
    """
    Whether holding these permissions justifies reaching this route family.

    Any permission inside the module grants entry, because the module's own
    authorization layer decides what the holder may actually do once inside.
    A full wildcard grants entry everywhere.
    """
    if not module:
        return False

    for permission in permissions:
        if permission.is_wildcard:
            return True
        if permission.app_name == module:
            return True

    return False

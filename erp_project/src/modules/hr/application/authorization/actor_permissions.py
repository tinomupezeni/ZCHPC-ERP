"""
Shared, superuser-aware permission resolution for HR application-layer
authorization checks.

Both role administration (modules.hr.api.views.organization_views) and
employee-assignment authorization (modules.hr.api.views.employee_views,
modules.hr.application.services.employee_service) need the same answer to
"what permissions does this caller have for this check" - including
respecting Django's existing is_superuser platform-level bypass, which
RBACMiddleware already grants unconditionally
(modules.identity.infrastructure.middleware.RBACMiddleware) but which
hr.Role.permissions cannot express on its own: a superuser account is not
guaranteed to have a linked Employees record at all (AUD-01 found one
live), so permission_set_for_user() alone would resolve such an account
to no permissions and incorrectly deny it.

This is the one place that logic lives; both callers import it rather
than each resolving it independently, which is what let the two paths
drift apart in the first place (REM-05 review finding).
"""

from modules.identity.domain.value_objects import PermissionSet
from modules.identity.infrastructure.route_access import permission_set_for_user


def resolve_actor_permissions(user) -> PermissionSet:
    """
    The effective permission set for an HR application-layer check.

    Superusers get PermissionSet.full_access(), independent of
    hr.Role.permissions, mirroring RBACMiddleware's own unconditional
    superuser bypass. Everyone else's permissions come from
    hr.Role.permissions via permission_set_for_user, the same
    authoritative source RBACMiddleware itself reads; PermissionSet.empty()
    is the fail-closed default when no role can be established.
    """
    if user.is_superuser:
        return PermissionSet.full_access()
    return permission_set_for_user(user) or PermissionSet.empty()

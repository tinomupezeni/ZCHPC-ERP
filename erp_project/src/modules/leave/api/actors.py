"""
Resolve the authenticated request into a LeaveActor.

The single place acting identity enters the leave application layer. Identity
comes from the authenticated user, never the request body; permissions come
from the shared ``resolve_actor_permissions`` (including its superuser
handling), not re-derived here.
"""

from modules.hr.application.authorization import resolve_actor_permissions
from modules.leave.application.authorization import LeaveActor


def leave_actor_from_request(request) -> LeaveActor:
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return LeaveActor.anonymous()

    # Reverse one-to-one: an AttributeError subclass when there is no profile.
    employee = getattr(user, "employee_profile", None)

    return LeaveActor(
        employee_id=employee.pk if employee else None,
        permissions=resolve_actor_permissions(user),
        is_superuser=bool(getattr(user, "is_superuser", False)),
        is_authenticated=True,
    )

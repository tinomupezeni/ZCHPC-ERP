"""
Resolve the authenticated request into a PayrollActor.

This is the single place where acting identity enters the payroll application
layer. It comes from the authenticated request user, never from the request
body. Permissions are resolved by the shared ``resolve_actor_permissions`` (the
same mechanism HR role/employee authorization uses, including its superuser
handling); nothing is re-derived here.
"""

from modules.hr.application.authorization import resolve_actor_permissions
from modules.payroll.application.authorization import PayrollActor


def payroll_actor_from_request(request) -> PayrollActor:
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return PayrollActor.anonymous()

    # Reverse one-to-one: an AttributeError subclass when there is no profile.
    employee = getattr(user, "employee_profile", None)

    return PayrollActor(
        employee_id=employee.pk if employee else None,
        permissions=resolve_actor_permissions(user),
        is_superuser=bool(getattr(user, "is_superuser", False)),
        is_authenticated=True,
    )

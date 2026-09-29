"""
Resolve the authenticated request into a Slice 4 Actor.

This is the single place where acting identity enters the procurement
application layer. Identity always comes from the authenticated request
context - never from the request body - so a client cannot act as anybody
other than themselves.

Authentication itself is unchanged: DRF/JWT populates ``request.user``, and the
employee behind that user is read through the existing ``employee_profile``
relation that the identity middleware and auth views already rely on.
"""

from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.application.authorization import Actor


def actor_from_request(request) -> Actor:
    """
    Build the acting :class:`Actor` from an authenticated DRF request.

    Returns the anonymous actor when the request carries no authenticated
    user; the application layer turns that into an authorization failure
    rather than the API deciding access here.
    """
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return Actor.anonymous()

    # Reverse one-to-one: Django raises an AttributeError subclass when the
    # user has no employee profile, so the default applies cleanly.
    employee = getattr(user, "employee_profile", None)
    role = getattr(employee, "role", None) if employee else None

    return Actor(
        employee_id=employee.pk if employee else None,
        permissions=PermissionSet.from_list(list(role.permissions or [])) if role else PermissionSet.empty(),
        department_id=employee.department_id if employee else None,
        role_name=role.name if role else "",
        user_id=user.pk,
        is_superuser=bool(getattr(user, "is_superuser", False)),
    )


def requester_identity(actor: Actor, employee) -> dict:
    """
    Describe the requester for a new purchase request, from the authenticated
    employee rather than anything the client supplied.
    """
    return {
        "requester_id": actor.employee_id,
        "requester_name": f"{employee.first_name} {employee.surname}".strip(),
        "department_id": employee.department_id,
        "department_name": employee.department.name if employee.department else "",
        "designation": employee.position.title if employee.position else "",
        "contact": employee.phone or employee.email or "",
    }

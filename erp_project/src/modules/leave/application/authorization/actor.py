"""
The authenticated actor, as the leave application layer sees them.

Resolved from the request by ``modules.leave.api.actors.leave_actor_from_request``
using the shared ``resolve_actor_permissions``; services and the policy never
touch ``request`` or ``request.user``. There is intentionally no role name here.
"""

from dataclasses import dataclass

from modules.identity.domain.value_objects import PermissionSet


@dataclass(frozen=True)
class LeaveActor:
    """
    Attributes:
        employee_id: ``hr.Employees`` primary key of the acting employee - the
            identifier ``LeaveRequest.employee_id`` and
            ``LeaveBalance.employee_id`` carry. None when the user has no
            employee profile (e.g. a bare superuser account).
        permissions: Effective permissions from ``resolve_actor_permissions``.
        is_superuser: Django superuser flag, preserved from the request user.
        is_authenticated: False only for the anonymous actor.
    """

    employee_id: int | None = None
    permissions: PermissionSet = PermissionSet.empty()
    is_superuser: bool = False
    is_authenticated: bool = True

    @classmethod
    def anonymous(cls) -> "LeaveActor":
        """An unauthenticated actor, denied every protected operation."""
        return cls(is_authenticated=False)

    def has_permission(self, permission: str) -> bool:
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        return self.permissions.has_permission(permission)

    def owns(self, employee_id: int | None) -> bool:
        """Whether the target belongs to this actor's own employee record."""
        return (
            self.is_authenticated
            and self.employee_id is not None
            and employee_id is not None
            and self.employee_id == employee_id
        )

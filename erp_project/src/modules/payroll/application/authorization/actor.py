"""
The authenticated actor, as the payroll application layer sees them.

Authentication and permission resolution happen upstream
(``modules.payroll.api.actors.payroll_actor_from_request`` using the shared
``resolve_actor_permissions``); this carries the resolved result so that
services and the policy never touch ``request`` or ``request.user``.

There is intentionally no role name here: payroll authorization is decided by
administrator-assigned capabilities, never by what a role happens to be called.
"""

from dataclasses import dataclass

from modules.identity.domain.value_objects import PermissionSet


@dataclass(frozen=True)
class PayrollActor:
    """
    Attributes:
        employee_id: ``hr.Employees`` primary key of the acting employee (the
            same identifier ``Payroll.employee_id`` and the other payroll
            tables use). None when the user has no employee profile, e.g. a
            bare superuser account.
        permissions: Effective permissions from ``resolve_actor_permissions``.
        is_superuser: Django superuser flag, preserved from the request user.
        is_authenticated: False only for the anonymous actor.
    """

    employee_id: int | None = None
    permissions: PermissionSet = PermissionSet.empty()
    is_superuser: bool = False
    is_authenticated: bool = True

    @classmethod
    def anonymous(cls) -> "PayrollActor":
        """An unauthenticated actor, denied every protected operation."""
        return cls(
            employee_id=None,
            permissions=PermissionSet.empty(),
            is_superuser=False,
            is_authenticated=False,
        )

    @classmethod
    def from_permissions(
        cls, permissions: PermissionSet, employee_id: int | None = None
    ) -> "PayrollActor":
        """
        Wrap an already-resolved PermissionSet (e.g. the ``actor_permissions``
        HR services already receive) as an authenticated actor.
        """
        return cls(employee_id=employee_id, permissions=permissions)

    def has_permission(self, permission: str) -> bool:
        """Whether the actor holds the capability."""
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        return self.permissions.has_permission(permission)

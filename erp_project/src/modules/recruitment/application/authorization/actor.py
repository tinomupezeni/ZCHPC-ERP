"""
The authenticated actor, as the recruitment application layer sees them.

Resolved from the request by
``modules.recruitment.api.actors.recruitment_actor_from_request`` using the
shared ``resolve_actor_permissions``; services and the policy never touch
``request`` or ``request.user``. There is intentionally no role name here.
"""

from dataclasses import dataclass

from modules.identity.domain.value_objects import PermissionSet


@dataclass(frozen=True)
class RecruitmentActor:
    """
    Attributes:
        permissions: Effective permissions from ``resolve_actor_permissions``.
        is_superuser: Django superuser flag, preserved from the request user.
        is_authenticated: False only for the anonymous actor.
    """

    permissions: PermissionSet = PermissionSet.empty()
    is_superuser: bool = False
    is_authenticated: bool = True

    @classmethod
    def anonymous(cls) -> "RecruitmentActor":
        """An unauthenticated actor, denied every internal operation."""
        return cls(is_authenticated=False)

    def has_permission(self, permission: str) -> bool:
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        return self.permissions.has_permission(permission)

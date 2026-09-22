"""
The authenticated actor, as the authorization layer sees them.

Authentication (JWT/session) and RBAC role resolution happen upstream; this
module only carries the resolved result into the application layer so that
policies never have to touch ``request.user`` or the ORM.
"""

from dataclasses import dataclass
from uuid import UUID

from modules.identity.domain.value_objects import PermissionSet

# Role names that bypass business-context scoping, matching the existing
# convention in identity (``Role.is_admin``) and the legacy procurement views.
ADMIN_ROLE_NAMES = frozenset({"ADMIN", "SYSTEM_ADMINISTRATOR"})


@dataclass(frozen=True)
class Actor:
    """
    An actor attempting a Purchase Request operation.

    Attributes:
        employee_id: ``hr.Employees`` primary key. None when the authenticated
            user has no employee profile (e.g. a bare superuser account).
        permissions: Capabilities granted by the actor's role.
        department_id: ``hr.Department`` the actor belongs to, when known.
        role_name: The actor's role name, used only for the admin bypass.
        user_id: The authenticated user's id, carried for auditing.
        is_superuser: Django superuser flag.
        is_authenticated: False only for the anonymous actor.
    """

    employee_id: int | None = None
    permissions: PermissionSet = PermissionSet.empty()
    department_id: int | None = None
    role_name: str = ""
    user_id: UUID | None = None
    is_superuser: bool = False
    is_authenticated: bool = True

    @classmethod
    def anonymous(cls) -> "Actor":
        """An unauthenticated actor, which is denied every protected operation."""
        return cls(
            employee_id=None,
            permissions=PermissionSet.empty(),
            is_authenticated=False,
        )

    @property
    def is_admin(self) -> bool:
        """Whether this actor bypasses business-context scoping."""
        return self.is_superuser or self.role_name.upper().strip() in ADMIN_ROLE_NAMES

    def has_permission(self, permission: str) -> bool:
        """Whether the actor's role grants the given capability."""
        if not self.is_authenticated:
            return False
        if self.is_admin:
            return True
        return self.permissions.has_permission(permission)

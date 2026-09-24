from modules.hr.application.authorization.actor_permissions import (
    resolve_actor_permissions,
)
from modules.hr.application.authorization.permissions import (
    EmployeeManagementPermissions,
    RoleManagementPermissions,
)

__all__ = [
    "EmployeeManagementPermissions",
    "RoleManagementPermissions",
    "resolve_actor_permissions",
]

"""
Role entity for authorization management.
"""

from dataclasses import dataclass
from typing import Any

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.identity.domain.value_objects import Permission, PermissionSet


@dataclass
class Role(AggregateRoot[int]):
    """
    Role aggregate root representing a user role with permissions.

    Roles define what actions users can perform in the system.

    Attributes:
        id: Unique identifier
        name: Role code (e.g., "ADMIN", "HR")
        display_name: Human-readable name
        description: Role description
        permissions: Set of permissions granted by this role
    """

    name: str
    display_name: str
    description: str
    permissions: PermissionSet

    def __init__(
        self,
        id: int,
        name: str,
        display_name: str,
        description: str = "",
        permissions: PermissionSet | None = None,
    ) -> None:
        """Initialize Role aggregate."""
        super().__init__(id)
        self._validate_name(name)
        self.name = name.upper().strip()
        self.display_name = display_name.strip()
        self.description = description.strip()
        self.permissions = permissions or PermissionSet.empty()

    @classmethod
    def create(
        cls,
        id: int,
        name: str,
        display_name: str,
        description: str = "",
        permissions: list[str] | None = None,
    ) -> "Role":
        """
        Factory method to create a new role.

        Args:
            id: Role ID
            name: Role code
            display_name: Human-readable name
            description: Role description
            permissions: List of permission strings
        """
        perm_set = (
            PermissionSet.from_list(permissions)
            if permissions
            else PermissionSet.empty()
        )
        return cls(
            id=id,
            name=name,
            display_name=display_name,
            description=description,
            permissions=perm_set,
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate role name format."""
        if not name:
            raise ValidationError(
                "Role name cannot be empty",
                code="EMPTY_ROLE_NAME",
            )
        if not name.replace("_", "").isalnum():
            raise ValidationError(
                "Role name must contain only alphanumeric characters and underscores",
                code="INVALID_ROLE_NAME",
                details={"name": name},
            )

    @property
    def is_admin(self) -> bool:
        """Check if this is an admin role with full access."""
        return self.name in ("ADMIN", "SYSTEM_ADMINISTRATOR")

    def has_permission(self, permission: str) -> bool:
        """
        Check if this role grants the specified permission.

        Args:
            permission: Permission string to check

        Returns:
            True if permission is granted
        """
        # Admin roles have all permissions
        if self.is_admin:
            return True
        return self.permissions.has_permission(permission)

    def has_any_permission(self, permissions: list[str]) -> bool:
        """
        Check if this role grants any of the specified permissions.

        Args:
            permissions: List of permission strings

        Returns:
            True if any permission is granted
        """
        if self.is_admin:
            return True
        return self.permissions.has_any_permission(permissions)

    def grant_permission(self, permission: str) -> None:
        """
        Grant a new permission to this role.

        Args:
            permission: Permission string to grant
        """
        current_perms = list(self.permissions.to_list())
        if permission not in current_perms:
            current_perms.append(permission)
            self.permissions = PermissionSet.from_list(current_perms)

    def revoke_permission(self, permission: str) -> None:
        """
        Revoke a permission from this role.

        Args:
            permission: Permission string to revoke
        """
        current_perms = self.permissions.to_list()
        if permission in current_perms:
            current_perms.remove(permission)
            self.permissions = PermissionSet.from_list(current_perms)

    def update(
        self,
        display_name: str | None = None,
        description: str | None = None,
    ) -> None:
        """
        Update role metadata.

        Args:
            display_name: New display name
            description: New description
        """
        if display_name is not None:
            self.display_name = display_name.strip()
        if description is not None:
            self.description = description.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": self.permissions.to_list(),
            "is_admin": self.is_admin,
        }


# Pre-defined role configurations
DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMIN": ["*"],
    "SYSTEM_ADMINISTRATOR": ["*"],
    "HUMAN_RESOURCES": [
        "hr.*",
        "human_resources.*",
        "payroll.*",
        "employees.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "ACCOUNTANT": [
        "payroll.*",
        "accounts.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "PROCUREMENT_OFFICER": [
        "procurement.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "SALES_REPRESENTATIVE": [
        "sales.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "DEPARTMENT_MANAGER": [
        "hr.view_*",
        "payroll.view_*",
        "reports.*",
        "employees.*",
        "authentication.*",
        "administration.*",
        "employee_portal.*",
    ],
    "REGULAR_STAFF": [
        "authentication.*",
        "self.*",
        "administration.*",
        "employee_portal.*",
    ],
    "INTERN": [
        "authentication.*",
        "self.*",
        "employee_portal.*",
    ],
}

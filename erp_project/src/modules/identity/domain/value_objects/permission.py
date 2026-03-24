"""
Permission and Role-related value objects.
"""

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
from typing import Any

from shared.domain.base import ValueObject
from shared.domain.exceptions import ValidationError


class RoleName(str, Enum):
    """Standard role names in the system."""

    ADMIN = "ADMIN"
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"
    HUMAN_RESOURCES = "HUMAN_RESOURCES"
    ACCOUNTANT = "ACCOUNTANT"
    PROCUREMENT_OFFICER = "PROCUREMENT_OFFICER"
    SALES_REPRESENTATIVE = "SALES_REPRESENTATIVE"
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER"
    REGULAR_STAFF = "REGULAR_STAFF"
    INTERN = "INTERN"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Permission(ValueObject):
    """
    Value object representing a single permission.

    Permissions follow the pattern: "app.action" or wildcards like "app.*"

    Examples:
        - "*" - Full access
        - "hr.*" - All HR permissions
        - "hr.view_employee" - Specific permission
        - "payroll.process" - Process payroll permission

    Attributes:
        value: The permission string
    """

    value: str

    def __post_init__(self) -> None:
        """Validate permission format."""
        if not self.value:
            raise ValidationError(
                "Permission cannot be empty",
                code="EMPTY_PERMISSION",
            )

        # Normalize to lowercase
        object.__setattr__(self, "value", self.value.strip().lower())

    @property
    def is_wildcard(self) -> bool:
        """Check if this is a full wildcard permission."""
        return self.value == "*"

    @property
    def is_app_wildcard(self) -> bool:
        """Check if this is an app-level wildcard (e.g., 'hr.*')."""
        return self.value.endswith(".*")

    @property
    def app_name(self) -> str | None:
        """Extract app name from permission."""
        if self.is_wildcard:
            return None
        parts = self.value.split(".")
        return parts[0] if parts else None

    def matches(self, required_permission: str) -> bool:
        """
        Check if this permission grants access to the required permission.

        Args:
            required_permission: The permission being checked

        Returns:
            True if this permission grants access
        """
        required = required_permission.lower().strip()

        # Full wildcard matches everything
        if self.is_wildcard:
            return True

        # Exact match
        if self.value == required:
            return True

        # App wildcard match (e.g., "hr.*" matches "hr.view_employee")
        if self.is_app_wildcard:
            app_prefix = self.value[:-1]  # Remove the "*"
            if required.startswith(app_prefix):
                return True

        # fnmatch pattern matching
        if fnmatch(required, self.value):
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"value": self.value}

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PermissionSet(ValueObject):
    """
    Value object representing a set of permissions.

    Provides methods to check if the set grants access to resources.

    Attributes:
        permissions: Tuple of Permission objects
    """

    permissions: tuple[Permission, ...]

    @classmethod
    def from_list(cls, permission_strings: list[str]) -> "PermissionSet":
        """
        Create PermissionSet from list of permission strings.

        Args:
            permission_strings: List of permission strings
        """
        perms = tuple(Permission(p) for p in permission_strings)
        return cls(permissions=perms)

    @classmethod
    def empty(cls) -> "PermissionSet":
        """Create an empty permission set."""
        return cls(permissions=())

    @classmethod
    def full_access(cls) -> "PermissionSet":
        """Create a permission set with full access."""
        return cls(permissions=(Permission("*"),))

    def has_permission(self, required: str) -> bool:
        """
        Check if this set grants the required permission.

        Args:
            required: The permission string to check

        Returns:
            True if any permission in the set grants access
        """
        return any(p.matches(required) for p in self.permissions)

    def has_any_permission(self, required_permissions: list[str]) -> bool:
        """
        Check if this set grants any of the required permissions.

        Args:
            required_permissions: List of permissions to check

        Returns:
            True if any required permission is granted
        """
        return any(self.has_permission(r) for r in required_permissions)

    def has_all_permissions(self, required_permissions: list[str]) -> bool:
        """
        Check if this set grants all required permissions.

        Args:
            required_permissions: List of permissions to check

        Returns:
            True if all required permissions are granted
        """
        return all(self.has_permission(r) for r in required_permissions)

    def to_list(self) -> list[str]:
        """Convert to list of permission strings."""
        return [p.value for p in self.permissions]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"permissions": self.to_list()}

    def __contains__(self, permission: str) -> bool:
        """Support 'in' operator for permission checking."""
        return self.has_permission(permission)

    def __len__(self) -> int:
        """Number of permissions in set."""
        return len(self.permissions)

    def __iter__(self):
        """Iterate over permissions."""
        return iter(self.permissions)

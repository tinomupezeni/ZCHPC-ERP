"""
Permission checker domain service.

Handles permission matching and authorization checks.
"""

from dataclasses import dataclass
from fnmatch import fnmatch

from modules.identity.domain.entities import Role
from modules.identity.domain.value_objects import PermissionSet


@dataclass
class PermissionChecker:
    """
    Domain service for checking permissions.

    Encapsulates the logic for matching permissions against
    required access patterns.
    """

    def check_permission(
        self,
        role: Role,
        required_permission: str,
    ) -> bool:
        """
        Check if a role has the required permission.

        Args:
            role: The user's role
            required_permission: Permission string to check

        Returns:
            True if permission is granted
        """
        return role.has_permission(required_permission)

    def check_any_permission(
        self,
        role: Role,
        required_permissions: list[str],
    ) -> bool:
        """
        Check if a role has any of the required permissions.

        Args:
            role: The user's role
            required_permissions: List of permissions (needs at least one)

        Returns:
            True if any permission is granted
        """
        return role.has_any_permission(required_permissions)

    def matches_pattern(self, permission: str, pattern: str) -> bool:
        """
        Check if a permission matches a pattern.

        Supports:
        - "*" - matches everything
        - "app.*" - matches all permissions in app
        - Exact matches
        - fnmatch patterns

        Args:
            permission: The required permission
            pattern: The pattern to match against

        Returns:
            True if pattern matches permission
        """
        # Full wildcard
        if pattern == "*":
            return True

        # Exact match
        if permission == pattern:
            return True

        # App wildcard (e.g., "hr.*" matches "hr.view_employee")
        if pattern.endswith(".*"):
            prefix = pattern[:-1]  # Remove "*"
            if permission.startswith(prefix):
                return True

        # fnmatch pattern matching
        if fnmatch(permission, pattern):
            return True

        return False

    def build_permission_string(self, app_name: str, action: str) -> str:
        """
        Build a permission string from components.

        Args:
            app_name: The application/module name
            action: The action being performed

        Returns:
            Permission string in format "app.action"
        """
        return f"{app_name.lower()}.{action.lower()}"


# Default permission checker instance
default_permission_checker = PermissionChecker()

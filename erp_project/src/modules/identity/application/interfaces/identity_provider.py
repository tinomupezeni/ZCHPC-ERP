"""
Identity provider interface for other modules.

This is the public contract that other modules use to
interact with the Identity module.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass
class UserDTO:
    """Data Transfer Object for user information."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_staff: bool
    is_superuser: bool


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    success: bool
    user: UserDTO | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    error: str | None = None


class IIdentityProvider(Protocol):
    """
    Interface for identity operations.

    Other modules depend on this interface, not concrete implementations.
    This allows the Identity module to be swapped or mocked.
    """

    def authenticate(self, email: str, password: str) -> AuthResult:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            AuthResult with tokens if successful
        """
        ...

    def get_user(self, user_id: UUID) -> UserDTO | None:
        """
        Get user information by ID.

        Args:
            user_id: User's UUID

        Returns:
            UserDTO or None if not found
        """
        ...

    def get_user_by_email(self, email: str) -> UserDTO | None:
        """
        Get user information by email.

        Args:
            email: User's email

        Returns:
            UserDTO or None if not found
        """
        ...

    def check_permission(self, user_id: UUID, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User's UUID
            permission: Permission string to check

        Returns:
            True if user has permission
        """
        ...


class ICurrentUserProvider(Protocol):
    """
    Interface for getting the current authenticated user.

    Used by request-scoped contexts to get the current user.
    """

    def get_current_user(self) -> UserDTO | None:
        """Get the currently authenticated user."""
        ...

    def get_current_user_id(self) -> UUID | None:
        """Get the current user's ID."""
        ...

    def get_current_permissions(self) -> list[str]:
        """Get the current user's permissions."""
        ...

    def has_permission(self, permission: str) -> bool:
        """Check if current user has a permission."""
        ...

    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated."""
        ...

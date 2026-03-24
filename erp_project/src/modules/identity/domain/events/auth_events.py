"""
Domain events for the Identity module.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from shared.domain.base import DomainEvent


@dataclass(frozen=True)
class UserCreatedEvent(DomainEvent):
    """Event raised when a new user is created."""

    user_id: UUID
    email: str


@dataclass(frozen=True)
class UserUpdatedEvent(DomainEvent):
    """Event raised when a user's profile is updated."""

    user_id: UUID
    email: str
    changes: tuple[str, ...]  # List of field names that changed


@dataclass(frozen=True)
class UserDeactivatedEvent(DomainEvent):
    """Event raised when a user account is deactivated."""

    user_id: UUID
    email: str
    deactivated_by: UUID | None = None


@dataclass(frozen=True)
class UserActivatedEvent(DomainEvent):
    """Event raised when a user account is activated."""

    user_id: UUID
    email: str
    activated_by: UUID | None = None


@dataclass(frozen=True)
class UserLockedEvent(DomainEvent):
    """Event raised when a user account is locked due to failed attempts."""

    user_id: UUID
    email: str
    locked_until: datetime


@dataclass(frozen=True)
class UserUnlockedEvent(DomainEvent):
    """Event raised when a user account is unlocked."""

    user_id: UUID
    email: str
    unlocked_by: UUID | None = None


@dataclass(frozen=True)
class LoginSucceededEvent(DomainEvent):
    """Event raised when a user successfully logs in."""

    user_id: UUID
    email: str
    ip_address: str


@dataclass(frozen=True)
class LoginFailedEvent(DomainEvent):
    """Event raised when a login attempt fails."""

    email: str
    ip_address: str
    reason: str
    user_id: UUID | None = None


@dataclass(frozen=True)
class PasswordChangedEvent(DomainEvent):
    """Event raised when a user changes their password."""

    user_id: UUID
    email: str
    changed_by: UUID | None = None  # None if self-change


@dataclass(frozen=True)
class RoleCreatedEvent(DomainEvent):
    """Event raised when a new role is created."""

    role_id: int
    role_name: str


@dataclass(frozen=True)
class RoleUpdatedEvent(DomainEvent):
    """Event raised when a role is updated."""

    role_id: int
    role_name: str
    changes: tuple[str, ...]


@dataclass(frozen=True)
class PermissionGrantedEvent(DomainEvent):
    """Event raised when a permission is granted to a role."""

    role_id: int
    role_name: str
    permission: str


@dataclass(frozen=True)
class PermissionRevokedEvent(DomainEvent):
    """Event raised when a permission is revoked from a role."""

    role_id: int
    role_name: str
    permission: str

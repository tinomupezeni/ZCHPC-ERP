"""
Identity module domain events.
"""

from modules.identity.domain.events.auth_events import (
    LoginFailedEvent,
    LoginSucceededEvent,
    PasswordChangedEvent,
    PermissionGrantedEvent,
    PermissionRevokedEvent,
    RoleCreatedEvent,
    RoleUpdatedEvent,
    UserActivatedEvent,
    UserCreatedEvent,
    UserDeactivatedEvent,
    UserLockedEvent,
    UserUnlockedEvent,
    UserUpdatedEvent,
)

__all__ = [
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeactivatedEvent",
    "UserActivatedEvent",
    "UserLockedEvent",
    "UserUnlockedEvent",
    "LoginSucceededEvent",
    "LoginFailedEvent",
    "PasswordChangedEvent",
    "RoleCreatedEvent",
    "RoleUpdatedEvent",
    "PermissionGrantedEvent",
    "PermissionRevokedEvent",
]

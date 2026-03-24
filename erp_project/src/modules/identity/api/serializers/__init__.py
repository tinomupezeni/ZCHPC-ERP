"""
Identity module API serializers.
"""

from modules.identity.api.serializers.auth_serializers import (
    AuditLogSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    RoleSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
)
from modules.identity.api.serializers.user_serializers import (
    ChangePasswordRequestSerializer,
    CreateUserRequestSerializer,
    CreateUserResponseSerializer,
    UpdateUserRequestSerializer,
    UserResponseSerializer,
)

__all__ = [
    # Auth
    "LoginRequestSerializer",
    "LoginResponseSerializer",
    "TokenRefreshRequestSerializer",
    "TokenRefreshResponseSerializer",
    "AuditLogSerializer",
    "RoleSerializer",
    # User
    "UserResponseSerializer",
    "CreateUserRequestSerializer",
    "CreateUserResponseSerializer",
    "UpdateUserRequestSerializer",
    "ChangePasswordRequestSerializer",
]

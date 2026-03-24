"""
Identity module application interfaces.

These define contracts for:
- Repository implementations
- Cross-module communication
"""

from modules.identity.application.interfaces.identity_provider import (
    AuthResult,
    ICurrentUserProvider,
    IIdentityProvider,
    UserDTO,
)
from modules.identity.application.interfaces.repositories import (
    IAuditLogRepository,
    IRoleRepository,
    IUserRepository,
)

__all__ = [
    # DTOs
    "UserDTO",
    "AuthResult",
    # Provider interfaces (for other modules)
    "IIdentityProvider",
    "ICurrentUserProvider",
    # Repository interfaces
    "IUserRepository",
    "IRoleRepository",
    "IAuditLogRepository",
]

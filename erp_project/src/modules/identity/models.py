"""
Identity module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.identity.infrastructure.persistence.models import (
    AuditLog,
    CustomUser,
    CustomUserManager,
)

__all__ = [
    "CustomUser",
    "CustomUserManager",
    "AuditLog",
]

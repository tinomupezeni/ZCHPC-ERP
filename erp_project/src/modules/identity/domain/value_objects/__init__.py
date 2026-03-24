"""
Identity module value objects.
"""

from modules.identity.domain.value_objects.password import HashedPassword
from modules.identity.domain.value_objects.permission import (
    Permission,
    PermissionSet,
    RoleName,
)

__all__ = [
    "HashedPassword",
    "Permission",
    "PermissionSet",
    "RoleName",
]

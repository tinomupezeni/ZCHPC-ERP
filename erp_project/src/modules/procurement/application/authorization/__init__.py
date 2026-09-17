"""
Authorization layer for the procurement application.

Keeps the "may this actor do this to this record?" decision out of both the
API layer and the PurchaseRequest aggregate.
"""

from modules.procurement.application.authorization.actor import (
    ADMIN_ROLE_NAMES,
    Actor,
)
from modules.procurement.application.authorization.permissions import (
    DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS,
    PurchaseRequestListScope,
    PurchaseRequestPermissions,
)
from modules.procurement.application.authorization.purchase_request_policy import (
    PurchaseRequestAuthorizationPolicy,
)

__all__ = [
    "Actor",
    "ADMIN_ROLE_NAMES",
    "PurchaseRequestPermissions",
    "PurchaseRequestListScope",
    "DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS",
    "PurchaseRequestAuthorizationPolicy",
]

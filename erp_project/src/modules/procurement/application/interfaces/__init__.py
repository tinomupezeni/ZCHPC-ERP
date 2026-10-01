"""
Application layer interfaces for the procurement module.
"""

from modules.procurement.application.interfaces.repositories import (
    ISupplierRepository,
    IInventoryItemRepository,
    IBudgetCenterRepository,
    IPurchaseRequestRepository,
    IPurchaseOrderRepository,
)

__all__ = [
    "ISupplierRepository",
    "IInventoryItemRepository",
    "IBudgetCenterRepository",
    "IPurchaseRequestRepository",
    "IPurchaseOrderRepository",
]

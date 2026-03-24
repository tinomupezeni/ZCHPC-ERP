"""
Domain events for the procurement module.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.events import DomainEvent


@dataclass(frozen=True)
class SupplierCreated(DomainEvent):
    """Event raised when a supplier is created."""

    supplier_id: int
    name: str
    email: str


@dataclass(frozen=True)
class SupplierDeactivated(DomainEvent):
    """Event raised when a supplier is deactivated."""

    supplier_id: int
    name: str


@dataclass(frozen=True)
class BudgetCenterCreated(DomainEvent):
    """Event raised when a budget center is created."""

    budget_center_id: int
    name: str
    code: str
    allocated_amount: Decimal


@dataclass(frozen=True)
class BudgetAllocated(DomainEvent):
    """Event raised when budget is allocated from a budget center."""

    budget_center_id: int
    request_id: int
    amount: Decimal
    remaining_amount: Decimal


@dataclass(frozen=True)
class BudgetReleased(DomainEvent):
    """Event raised when allocated budget is released."""

    budget_center_id: int
    request_id: int
    amount: Decimal


@dataclass(frozen=True)
class PurchaseRequestCreated(DomainEvent):
    """Event raised when a purchase request is created."""

    request_id: int
    requester_id: int
    supplier_id: int
    budget_center_id: int
    total_amount: Decimal


@dataclass(frozen=True)
class PurchaseRequestLevel1Approved(DomainEvent):
    """Event raised when a purchase request receives Level 1 approval."""

    request_id: int
    approver_id: int
    total_amount: Decimal


@dataclass(frozen=True)
class PurchaseRequestLevel2Approved(DomainEvent):
    """Event raised when a purchase request receives Level 2 approval."""

    request_id: int
    approver_id: int
    total_amount: Decimal
    order_number: str


@dataclass(frozen=True)
class PurchaseRequestRejected(DomainEvent):
    """Event raised when a purchase request is rejected."""

    request_id: int
    rejector_id: int
    reason: Optional[str]


@dataclass(frozen=True)
class PurchaseOrderCreated(DomainEvent):
    """Event raised when a purchase order is created."""

    order_id: int
    order_number: str
    request_id: int
    supplier_id: int
    total_amount: Decimal


@dataclass(frozen=True)
class PurchaseOrderSent(DomainEvent):
    """Event raised when a purchase order is sent to supplier."""

    order_id: int
    order_number: str
    supplier_id: int


@dataclass(frozen=True)
class GoodsReceived(DomainEvent):
    """Event raised when goods are received for a purchase order."""

    order_id: int
    order_number: str
    is_partial: bool


@dataclass(frozen=True)
class PurchaseOrderCancelled(DomainEvent):
    """Event raised when a purchase order is cancelled."""

    order_id: int
    order_number: str
    reason: Optional[str]


@dataclass(frozen=True)
class InventoryItemCreated(DomainEvent):
    """Event raised when an inventory item is created."""

    item_id: int
    sku: str
    name: str


@dataclass(frozen=True)
class InventoryStockUpdated(DomainEvent):
    """Event raised when inventory stock is updated."""

    item_id: int
    sku: str
    old_quantity: int
    new_quantity: int
    change: int

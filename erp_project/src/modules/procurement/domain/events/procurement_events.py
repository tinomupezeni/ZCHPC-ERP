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
    """
    Event raised when a purchase request is rejected (Slice 3 notifications).

    Fields were realigned to the current multi-stage-approval PurchaseRequest
    aggregate (requisition_number, requester_id) - this event was previously
    defined but never instantiated anywhere, so there was no live usage to
    preserve compatibility with.
    """

    request_id: int
    requisition_number: str
    requester_id: int
    rejector_id: int
    reason: str


@dataclass(frozen=True)
class PurchaseRequestProcessed(DomainEvent):
    """Event raised when procurement completes processing a purchase request (Slice 3 notifications)."""

    request_id: int
    requisition_number: str
    requester_id: int
    processed_by: int


@dataclass(frozen=True)
class PurchaseRequestCorrectedAndResubmitted(DomainEvent):
    """
    Event raised when a previously rejected purchase request is resubmitted
    (F19 notifications).

    Raised by PurchaseRequest.submit() itself, not by correct_and_resubmit()
    - correct_and_resubmit() only ever returns a REJECTED request to DRAFT;
    it is the following submit() call that actually re-enters the workflow
    at PENDING_DEPARTMENT_HEAD, so that is the one place that can tell a
    corrected resubmission apart from a first-time submission (see
    PurchaseRequest.submit()'s own docstring for how).

    Carries department_id (not a resolved department-head employee id):
    the aggregate has no way to look up who currently heads that
    department - resolving that recipient is an infrastructure concern for
    whichever handler consumes this event, not something the domain layer
    can or should know.
    """

    request_id: int
    requisition_number: str
    requester_id: int
    department_id: int


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

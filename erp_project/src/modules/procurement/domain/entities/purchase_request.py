"""
PurchaseRequest aggregate root with line items.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot, Entity
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.value_objects import RequestStatus


@dataclass
class PurchaseRequestItem(Entity[int]):
    """
    Entity representing a line item in a purchase request.
    """

    request_id: Optional[int]
    item_id: int
    item_name: str
    quantity: int
    price_per_unit: Decimal

    def __post_init__(self) -> None:
        """Validate request item."""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
        if self.price_per_unit < 0:
            raise ValidationError("Price cannot be negative")

    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost for this line item."""
        return (self.price_per_unit * self.quantity).quantize(Decimal("0.01"))

    @classmethod
    def create(
        cls,
        item_id: int,
        item_name: str,
        quantity: int,
        price_per_unit: Decimal
    ) -> "PurchaseRequestItem":
        """Factory method to create a request item."""
        return cls(
            id=None,
            request_id=None,
            item_id=item_id,
            item_name=item_name,
            quantity=quantity,
            price_per_unit=price_per_unit
        )


@dataclass
class PurchaseRequest(AggregateRoot[int]):
    """
    Aggregate root for purchase requests.

    Represents a request to purchase items from a supplier.
    Supports multi-level approval workflow.
    """

    requester_id: int
    requester_name: str
    supplier_id: int
    budget_center_id: int
    status: RequestStatus = RequestStatus.PENDING
    items: List[PurchaseRequestItem] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    level1_approved_by: Optional[int] = None
    level1_approved_at: Optional[datetime] = None
    level2_approved_by: Optional[int] = None
    level2_approved_at: Optional[datetime] = None
    rejected_by: Optional[int] = None
    rejected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate purchase request."""
        if not self.requester_name or not self.requester_name.strip():
            raise ValidationError("Requester name is required")

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount of all items."""
        return sum(
            (item.total_cost for item in self.items),
            Decimal("0")
        )

    @property
    def item_count(self) -> int:
        """Get number of line items."""
        return len(self.items)

    @property
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == RequestStatus.PENDING

    @property
    def is_level1_approved(self) -> bool:
        """Check if Level 1 approved."""
        return self.status == RequestStatus.LEVEL1_APPROVED

    @property
    def is_fully_approved(self) -> bool:
        """Check if fully approved."""
        return self.status == RequestStatus.LEVEL2_APPROVED

    @property
    def is_rejected(self) -> bool:
        """Check if rejected."""
        return self.status == RequestStatus.REJECTED

    @property
    def is_final(self) -> bool:
        """Check if status is terminal."""
        return self.status.is_final

    def add_item(self, item: PurchaseRequestItem) -> None:
        """Add an item to the request."""
        if self.is_final:
            raise ValidationError("Cannot modify a finalized request")
        item.request_id = self.id
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_item(self, item_id: int) -> bool:
        """Remove an item by ID."""
        if self.is_final:
            raise ValidationError("Cannot modify a finalized request")
        for i, item in enumerate(self.items):
            if item.item_id == item_id:
                self.items.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def clear_items(self) -> None:
        """Remove all items."""
        if self.is_final:
            raise ValidationError("Cannot modify a finalized request")
        self.items.clear()
        self.updated_at = datetime.now()

    def approve_level1(self, approver_id: int) -> None:
        """
        Approve at Level 1 (manager approval).

        Args:
            approver_id: ID of the approving manager

        Raises:
            ValidationError: If not in correct state
        """
        if not self.status.can_approve_level1:
            raise ValidationError(
                f"Cannot approve Level 1. Current status: {self.status.value}"
            )
        if not self.items:
            raise ValidationError("Cannot approve request with no items")

        self.status = RequestStatus.LEVEL1_APPROVED
        self.level1_approved_by = approver_id
        self.level1_approved_at = datetime.now()
        self.updated_at = datetime.now()

    def approve_level2(self, approver_id: int) -> None:
        """
        Approve at Level 2 (finance/senior management approval).

        This is the final approval that allows PO creation.

        Args:
            approver_id: ID of the approving manager

        Raises:
            ValidationError: If not in correct state
        """
        if not self.status.can_approve_level2:
            raise ValidationError(
                f"Cannot approve Level 2. Current status: {self.status.value}"
            )

        self.status = RequestStatus.LEVEL2_APPROVED
        self.level2_approved_by = approver_id
        self.level2_approved_at = datetime.now()
        self.updated_at = datetime.now()

    def reject(self, rejector_id: int, reason: Optional[str] = None) -> None:
        """
        Reject the purchase request.

        Args:
            rejector_id: ID of the person rejecting
            reason: Optional reason for rejection

        Raises:
            ValidationError: If not in correct state
        """
        if not self.status.can_reject:
            raise ValidationError(
                f"Cannot reject. Current status: {self.status.value}"
            )

        self.status = RequestStatus.REJECTED
        self.rejected_by = rejector_id
        self.rejected_at = datetime.now()
        self.rejection_reason = reason
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the purchase request."""
        if self.is_final:
            raise ValidationError("Cannot cancel a finalized request")
        self.status = RequestStatus.CANCELLED
        self.updated_at = datetime.now()

    def validate(self) -> None:
        """Validate the request before processing."""
        if not self.items:
            raise ValidationError("Purchase request must have at least one item")
        if self.total_amount <= Decimal("0"):
            raise ValidationError("Total amount must be positive")

    @classmethod
    def create(
        cls,
        requester_id: int,
        requester_name: str,
        supplier_id: int,
        budget_center_id: int
    ) -> "PurchaseRequest":
        """Factory method to create a purchase request."""
        now = datetime.now()
        return cls(
            id=None,
            requester_id=requester_id,
            requester_name=requester_name,
            supplier_id=supplier_id,
            budget_center_id=budget_center_id,
            status=RequestStatus.PENDING,
            items=[],
            created_at=now,
            updated_at=now
        )

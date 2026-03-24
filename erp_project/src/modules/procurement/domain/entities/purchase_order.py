"""
PurchaseOrder aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.value_objects import OrderStatus, OrderNumber


@dataclass
class PurchaseOrder(AggregateRoot[int]):
    """
    Aggregate root for purchase orders.

    Created after a PurchaseRequest is fully approved.
    Represents a formal order to a supplier.
    """

    order_number: str
    request_id: int
    supplier_id: int
    total_amount: Decimal
    status: OrderStatus = OrderStatus.DRAFT
    delivered: bool = False
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate purchase order."""
        if not self.order_number:
            raise ValidationError("Order number is required")
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative")

    @property
    def order_number_value(self) -> OrderNumber:
        """Get as OrderNumber value object."""
        return OrderNumber(value=self.order_number)

    @property
    def is_draft(self) -> bool:
        """Check if order is draft."""
        return self.status == OrderStatus.DRAFT

    @property
    def is_sent(self) -> bool:
        """Check if order is sent."""
        return self.status == OrderStatus.SENT

    @property
    def is_received(self) -> bool:
        """Check if order is fully received."""
        return self.status == OrderStatus.RECEIVED

    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == OrderStatus.CANCELLED

    @property
    def can_be_sent(self) -> bool:
        """Check if order can be sent to supplier."""
        return self.status == OrderStatus.DRAFT

    @property
    def can_receive_goods(self) -> bool:
        """Check if order can receive goods."""
        return self.status.can_receive

    def send_to_supplier(self) -> None:
        """Mark order as sent to supplier."""
        if not self.can_be_sent:
            raise ValidationError(
                f"Cannot send order. Current status: {self.status.value}"
            )
        self.status = OrderStatus.SENT
        self.sent_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_partially_received(self) -> None:
        """Mark order as partially received."""
        if not self.can_receive_goods:
            raise ValidationError(
                f"Cannot mark as received. Current status: {self.status.value}"
            )
        self.status = OrderStatus.PARTIALLY_RECEIVED
        self.updated_at = datetime.now()

    def mark_fully_received(self) -> None:
        """Mark order as fully received."""
        if not self.can_receive_goods:
            raise ValidationError(
                f"Cannot mark as received. Current status: {self.status.value}"
            )
        self.status = OrderStatus.RECEIVED
        self.delivered = True
        self.received_at = datetime.now()
        self.updated_at = datetime.now()

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the purchase order."""
        if self.is_received:
            raise ValidationError("Cannot cancel a received order")
        if self.is_cancelled:
            raise ValidationError("Order is already cancelled")
        self.status = OrderStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"
        self.updated_at = datetime.now()

    def add_notes(self, notes: str) -> None:
        """Add notes to the order."""
        self.notes = notes
        self.updated_at = datetime.now()

    @classmethod
    def create_from_request(
        cls,
        request_id: int,
        supplier_id: int,
        total_amount: Decimal,
        order_number: Optional[str] = None
    ) -> "PurchaseOrder":
        """
        Factory method to create a PO from an approved request.

        Args:
            request_id: ID of the approved purchase request
            supplier_id: ID of the supplier
            total_amount: Total order amount
            order_number: Optional order number (generated if not provided)

        Returns:
            New PurchaseOrder
        """
        if order_number is None:
            order_number = OrderNumber.generate().value

        now = datetime.now()
        return cls(
            id=None,
            order_number=order_number,
            request_id=request_id,
            supplier_id=supplier_id,
            total_amount=total_amount,
            status=OrderStatus.DRAFT,
            delivered=False,
            created_at=now,
            updated_at=now
        )

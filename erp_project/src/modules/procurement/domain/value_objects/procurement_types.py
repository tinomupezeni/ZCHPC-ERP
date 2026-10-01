"""
Procurement domain value objects and enums.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.domain.base import ValueObject


class RequestStatus(str, Enum):
    """Status of a purchase request."""

    PENDING = "Pending"
    LEVEL1_APPROVED = "Level1Approved"
    LEVEL2_APPROVED = "Level2Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"

    @property
    def is_pending(self) -> bool:
        """Check if status is pending."""
        return self == RequestStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if fully approved."""
        return self == RequestStatus.LEVEL2_APPROVED

    @property
    def is_final(self) -> bool:
        """Check if status is terminal."""
        return self in (
            RequestStatus.LEVEL2_APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.CANCELLED
        )

    @property
    def can_approve_level1(self) -> bool:
        """Check if Level 1 approval is allowed."""
        return self == RequestStatus.PENDING

    @property
    def can_approve_level2(self) -> bool:
        """Check if Level 2 approval is allowed."""
        return self == RequestStatus.LEVEL1_APPROVED

    @property
    def can_reject(self) -> bool:
        """Check if rejection is allowed."""
        return self in (RequestStatus.PENDING, RequestStatus.LEVEL1_APPROVED)


class OrderStatus(str, Enum):
    """Status of a purchase order."""

    DRAFT = "Draft"
    SENT = "Sent"
    PARTIALLY_RECEIVED = "PartiallyReceived"
    RECEIVED = "Received"
    CANCELLED = "Cancelled"

    @property
    def is_draft(self) -> bool:
        """Check if order is draft."""
        return self == OrderStatus.DRAFT

    @property
    def is_received(self) -> bool:
        """Check if order is fully received."""
        return self == OrderStatus.RECEIVED

    @property
    def can_receive(self) -> bool:
        """Check if order can receive goods."""
        return self in (OrderStatus.SENT, OrderStatus.PARTIALLY_RECEIVED)


@dataclass(frozen=True)
class Money(ValueObject):
    """
    Immutable value object representing monetary amount.

    Always stored in base currency (USD).
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate money."""
        if self.amount < 0:
            from shared.domain.exceptions import ValidationError
            raise ValidationError("Amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: int) -> "Money":
        return Money(
            amount=(self.amount * Decimal(str(factor))).quantize(Decimal("0.01")),
            currency=self.currency
        )

    @property
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0")

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create zero money."""
        return cls(amount=Decimal("0"), currency=currency)


@dataclass(frozen=True)
class VendorRating(ValueObject):
    """
    Value object representing vendor rating.

    Scale: 0.00 to 5.00
    """

    value: Decimal

    def __post_init__(self) -> None:
        """Validate rating."""
        if self.value < Decimal("0") or self.value > Decimal("5"):
            from shared.domain.exceptions import ValidationError
            raise ValidationError("Rating must be between 0 and 5")

    @property
    def is_good(self) -> bool:
        """Check if rating is good (3+)."""
        return self.value >= Decimal("3")

    @property
    def is_excellent(self) -> bool:
        """Check if rating is excellent (4+)."""
        return self.value >= Decimal("4")

    @classmethod
    def default(cls) -> "VendorRating":
        """Create default rating."""
        return cls(value=Decimal("0"))


@dataclass(frozen=True)
class OrderNumber(ValueObject):
    """
    Value object representing a purchase order number.

    Format: PO-XXXXXXXX (8 random alphanumeric characters)
    """

    value: str

    def __post_init__(self) -> None:
        """Validate order number."""
        if not self.value or not self.value.startswith("PO-"):
            from shared.domain.exceptions import ValidationError
            raise ValidationError("Order number must start with 'PO-'")

    @classmethod
    def generate(cls) -> "OrderNumber":
        """Generate a new order number."""
        import secrets
        suffix = secrets.token_hex(4).upper()
        return cls(value=f"PO-{suffix}")


@dataclass(frozen=True)
class SKU(ValueObject):
    """
    Value object representing a Stock Keeping Unit.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate SKU."""
        if not self.value or len(self.value) > 50:
            from shared.domain.exceptions import ValidationError
            raise ValidationError("SKU must be 1-50 characters")


@dataclass(frozen=True)
class BudgetAllocation(ValueObject):
    """
    Value object representing budget allocation details.
    """

    allocated_amount: Decimal
    used_amount: Decimal

    def __post_init__(self) -> None:
        """Validate allocation."""
        if self.allocated_amount < 0:
            from shared.domain.exceptions import ValidationError
            raise ValidationError("Allocated amount cannot be negative")
        if self.used_amount < 0:
            from shared.domain.exceptions import ValidationError
            raise ValidationError("Used amount cannot be negative")

    @property
    def remaining_amount(self) -> Decimal:
        """Get remaining budget."""
        return self.allocated_amount - self.used_amount

    @property
    def utilization_rate(self) -> Decimal:
        """Get budget utilization rate as percentage."""
        if self.allocated_amount == Decimal("0"):
            return Decimal("0")
        return (self.used_amount / self.allocated_amount * 100).quantize(
            Decimal("0.01")
        )

    @property
    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.remaining_amount <= Decimal("0")

    def can_allocate(self, amount: Decimal) -> bool:
        """Check if amount can be allocated from remaining budget."""
        return self.remaining_amount >= amount

    def allocate(self, amount: Decimal) -> "BudgetAllocation":
        """Create new allocation with amount allocated."""
        if not self.can_allocate(amount):
            from shared.domain.exceptions import ValidationError
            raise ValidationError(
                f"Insufficient budget. Requested: {amount}, Available: {self.remaining_amount}"
            )
        return BudgetAllocation(
            allocated_amount=self.allocated_amount,
            used_amount=self.used_amount + amount
        )

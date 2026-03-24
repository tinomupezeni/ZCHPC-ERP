"""
BudgetCenter aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.value_objects import BudgetAllocation


@dataclass
class BudgetCenter(AggregateRoot[int]):
    """
    Aggregate root for budget centers.

    Represents a cost center or department with allocated budget.
    """

    name: str
    code: str
    allocated_amount: Decimal
    used_amount: Decimal = Decimal("0")
    fiscal_year: int = 2024
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate budget center."""
        if not self.name or not self.name.strip():
            raise ValidationError("Budget center name is required")
        if not self.code or not self.code.strip():
            raise ValidationError("Budget center code is required")
        if self.allocated_amount < 0:
            raise ValidationError("Allocated amount cannot be negative")
        if self.used_amount < 0:
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

    @property
    def allocation(self) -> BudgetAllocation:
        """Get as BudgetAllocation value object."""
        return BudgetAllocation(
            allocated_amount=self.allocated_amount,
            used_amount=self.used_amount
        )

    def has_sufficient_budget(self, amount: Decimal) -> bool:
        """Check if there's sufficient budget for an amount."""
        return self.remaining_amount >= amount

    def allocate(self, amount: Decimal) -> None:
        """
        Allocate budget for a purchase.

        Args:
            amount: Amount to allocate

        Raises:
            ValidationError: If insufficient budget
        """
        if amount <= 0:
            raise ValidationError("Amount to allocate must be positive")
        if not self.has_sufficient_budget(amount):
            raise ValidationError(
                f"Insufficient budget. Requested: {amount}, "
                f"Available: {self.remaining_amount}"
            )
        self.used_amount += amount
        self.updated_at = datetime.now()

    def release(self, amount: Decimal) -> None:
        """
        Release allocated budget (e.g., when request is cancelled).

        Args:
            amount: Amount to release
        """
        if amount <= 0:
            raise ValidationError("Amount to release must be positive")
        if amount > self.used_amount:
            raise ValidationError("Cannot release more than used amount")
        self.used_amount -= amount
        self.updated_at = datetime.now()

    def increase_allocation(self, amount: Decimal) -> None:
        """Increase total budget allocation."""
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        self.allocated_amount += amount
        self.updated_at = datetime.now()

    def update_details(
        self,
        name: Optional[str] = None,
        code: Optional[str] = None
    ) -> None:
        """Update budget center details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Name cannot be empty")
            self.name = name.strip()
        if code is not None:
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            self.code = code.strip().upper()
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate this budget center."""
        self.is_active = False
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        allocated_amount: Decimal,
        fiscal_year: int = 2024
    ) -> "BudgetCenter":
        """Factory method to create a budget center."""
        now = datetime.now()
        return cls(
            id=None,
            name=name.strip(),
            code=code.strip().upper(),
            allocated_amount=allocated_amount,
            used_amount=Decimal("0"),
            fiscal_year=fiscal_year,
            is_active=True,
            created_at=now,
            updated_at=now
        )

"""
Currency aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


@dataclass
class Currency(AggregateRoot[int]):
    """
    Aggregate root for currencies.

    Represents a currency with exchange rate to base currency.
    """

    code: str  # e.g., USD, EUR, ZIG
    name: str
    symbol: Optional[str] = None
    rate_to_base: Decimal = Decimal("1")
    is_base: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate currency."""
        if not self.code or len(self.code) < 2:
            raise ValidationError("Currency code must be at least 2 characters")
        if not self.name:
            raise ValidationError("Currency name is required")
        if self.rate_to_base <= 0:
            raise ValidationError("Exchange rate must be positive")

    def update_rate(self, new_rate: Decimal) -> None:
        """Update the exchange rate."""
        if new_rate <= 0:
            raise ValidationError("Exchange rate must be positive")
        if self.is_base:
            raise ValidationError("Cannot change rate of base currency")
        self.rate_to_base = new_rate
        self.updated_at = datetime.now()

    def convert_to_base(self, amount: Decimal) -> Decimal:
        """Convert amount from this currency to base currency."""
        return (amount * self.rate_to_base).quantize(Decimal("0.01"))

    def convert_from_base(self, amount: Decimal) -> Decimal:
        """Convert amount from base currency to this currency."""
        if self.rate_to_base == 0:
            raise ValidationError("Cannot convert with zero exchange rate")
        return (amount / self.rate_to_base).quantize(Decimal("0.01"))

    def set_as_base(self) -> None:
        """Set this currency as the base currency."""
        self.is_base = True
        self.rate_to_base = Decimal("1")

    def deactivate(self) -> None:
        """Deactivate this currency."""
        if self.is_base:
            raise ValidationError("Cannot deactivate base currency")
        self.is_active = False

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        symbol: Optional[str] = None,
        rate_to_base: Decimal = Decimal("1"),
        is_base: bool = False
    ) -> "Currency":
        """Factory method to create a currency."""
        now = datetime.now()
        return cls(
            id=None,
            code=code.upper(),
            name=name,
            symbol=symbol,
            rate_to_base=rate_to_base,
            is_base=is_base,
            is_active=True,
            created_at=now,
            updated_at=now
        )

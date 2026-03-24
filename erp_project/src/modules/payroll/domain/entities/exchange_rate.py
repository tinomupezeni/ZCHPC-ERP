"""
ExchangeRate aggregate root for currency conversion.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import Currency


@dataclass
class ExchangeRate(AggregateRoot[int]):
    """
    Aggregate root for daily exchange rates.

    Stores the ZIG to USD conversion rate for a specific date.
    Used for dual-currency payroll calculations.
    """

    rate_date: date
    zig_to_usd_rate: Decimal  # How many USD for 1 ZIG (typically < 1)
    source: Optional[str] = None  # Source of rate (e.g., "RBZ", "Zimpricecheck")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate exchange rate."""
        if self.zig_to_usd_rate <= 0:
            raise ValidationError("Exchange rate must be positive")

    @property
    def usd_to_zig_rate(self) -> Decimal:
        """Get the inverse rate (USD to ZIG)."""
        return (Decimal("1") / self.zig_to_usd_rate).quantize(Decimal("0.00000001"))

    def convert_zig_to_usd(self, amount_zig: Decimal) -> Decimal:
        """
        Convert ZIG amount to USD.

        Args:
            amount_zig: Amount in ZIG

        Returns:
            Equivalent amount in USD
        """
        if amount_zig == 0:
            return Decimal("0")
        return (amount_zig * self.zig_to_usd_rate).quantize(Decimal("0.01"))

    def convert_usd_to_zig(self, amount_usd: Decimal) -> Decimal:
        """
        Convert USD amount to ZIG.

        Args:
            amount_usd: Amount in USD

        Returns:
            Equivalent amount in ZIG
        """
        if amount_usd == 0:
            return Decimal("0")
        return (amount_usd / self.zig_to_usd_rate).quantize(Decimal("0.01"))

    def update_rate(self, new_rate: Decimal, source: Optional[str] = None) -> None:
        """
        Update the exchange rate.

        Args:
            new_rate: New ZIG to USD rate
            source: Source of the new rate
        """
        if new_rate <= 0:
            raise ValidationError("Exchange rate must be positive")
        self.zig_to_usd_rate = new_rate
        if source:
            self.source = source
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        rate_date: date,
        zig_to_usd_rate: Decimal,
        source: Optional[str] = None
    ) -> "ExchangeRate":
        """
        Factory method to create an exchange rate.

        Args:
            rate_date: Date for this rate
            zig_to_usd_rate: ZIG to USD conversion rate
            source: Source of the rate
        """
        return cls(
            id=None,
            rate_date=rate_date,
            zig_to_usd_rate=zig_to_usd_rate,
            source=source,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @property
    def display_rate(self) -> str:
        """Human-readable format: '1 USD = X ZIG'."""
        return f"1 USD = {self.usd_to_zig_rate:.4f} ZIG"

    @property
    def inverse_display(self) -> str:
        """Alternative format: '1 ZIG = X USD'."""
        return f"1 ZIG = {self.zig_to_usd_rate:.8f} USD"

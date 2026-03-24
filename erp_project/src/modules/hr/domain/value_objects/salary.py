"""
Salary value object for multi-currency support.
"""

from dataclasses import dataclass
from decimal import Decimal

from shared.domain.base import ValueObject
from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import Money, Currency


@dataclass(frozen=True)
class Salary(ValueObject):
    """
    Multi-currency salary information.

    Represents an employee's salary in both USD and ZIG currencies.
    At least one currency amount must be specified.

    Attributes:
        usd_amount: Salary in USD (can be 0)
        zig_amount: Salary in ZIG (can be 0)
    """

    usd_amount: Decimal
    zig_amount: Decimal

    def __post_init__(self):
        """Validate salary amounts."""
        if self.usd_amount < 0:
            raise ValidationError(
                message="USD salary cannot be negative",
                code="NEGATIVE_SALARY",
            )
        if self.zig_amount < 0:
            raise ValidationError(
                message="ZIG salary cannot be negative",
                code="NEGATIVE_SALARY",
            )
        if self.usd_amount == 0 and self.zig_amount == 0:
            raise ValidationError(
                message="At least one salary amount must be greater than zero",
                code="ZERO_SALARY",
            )

    @classmethod
    def create(
        cls,
        usd_amount: Decimal | float | int | str | None = None,
        zig_amount: Decimal | float | int | str | None = None,
    ) -> "Salary":
        """
        Create a Salary from various input types.

        Args:
            usd_amount: USD salary amount
            zig_amount: ZIG salary amount

        Returns:
            New Salary instance
        """
        usd = Decimal(str(usd_amount or 0))
        zig = Decimal(str(zig_amount or 0))
        return cls(usd_amount=usd, zig_amount=zig)

    @classmethod
    def usd_only(cls, amount: Decimal | float | int | str) -> "Salary":
        """Create a USD-only salary."""
        return cls(usd_amount=Decimal(str(amount)), zig_amount=Decimal("0"))

    @classmethod
    def zig_only(cls, amount: Decimal | float | int | str) -> "Salary":
        """Create a ZIG-only salary."""
        return cls(usd_amount=Decimal("0"), zig_amount=Decimal(str(amount)))

    @property
    def usd(self) -> Money:
        """Get USD salary as Money."""
        return Money.usd(self.usd_amount)

    @property
    def zig(self) -> Money:
        """Get ZIG salary as Money."""
        return Money.zig(self.zig_amount)

    @property
    def has_usd(self) -> bool:
        """Check if salary has a USD component."""
        return self.usd_amount > 0

    @property
    def has_zig(self) -> bool:
        """Check if salary has a ZIG component."""
        return self.zig_amount > 0

    def total_in_usd(self, exchange_rate: Decimal) -> Money:
        """
        Calculate total salary in USD.

        Args:
            exchange_rate: ZIG to USD exchange rate

        Returns:
            Total salary in USD
        """
        zig_in_usd = self.zig_amount / exchange_rate if exchange_rate > 0 else Decimal("0")
        return Money.usd(self.usd_amount + zig_in_usd)

    def with_increase(self, usd_increase: Decimal = Decimal("0"), zig_increase: Decimal = Decimal("0")) -> "Salary":
        """
        Create a new salary with increases applied.

        Args:
            usd_increase: USD increase amount
            zig_increase: ZIG increase amount

        Returns:
            New Salary with increases
        """
        return Salary(
            usd_amount=self.usd_amount + usd_increase,
            zig_amount=self.zig_amount + zig_increase,
        )

    def with_percentage_increase(self, percentage: Decimal) -> "Salary":
        """
        Create a new salary with a percentage increase.

        Args:
            percentage: Percentage to increase (e.g., 10 for 10%)

        Returns:
            New Salary with percentage increase
        """
        multiplier = Decimal("1") + (percentage / Decimal("100"))
        return Salary(
            usd_amount=self.usd_amount * multiplier,
            zig_amount=self.zig_amount * multiplier,
        )

    def __str__(self) -> str:
        """String representation."""
        parts = []
        if self.has_usd:
            parts.append(f"${self.usd_amount:,.2f}")
        if self.has_zig:
            parts.append(f"ZIG {self.zig_amount:,.2f}")
        return " + ".join(parts) if parts else "$0.00"

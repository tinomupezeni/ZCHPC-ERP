"""
Money value object for financial calculations.

Handles monetary amounts with currency, providing safe arithmetic
operations and preventing currency mismatch errors.

Example:
    salary_usd = Money(Decimal("1500.00"), Currency.USD)
    bonus = Money(Decimal("200.00"), Currency.USD)
    total = salary_usd.add(bonus)  # Money(1700.00, USD)
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


class Currency(str, Enum):
    """Supported currencies in the ERP system."""

    USD = "USD"
    ZIG = "ZIG"  # Zimbabwe Gold (ZiG)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money(ValueObject):
    """
    Value object representing a monetary amount.

    Money is immutable and operations return new Money instances.
    Currency mismatches raise ValidationError.

    Attributes:
        amount: The monetary amount (stored as Decimal for precision)
        currency: The currency of the amount

    Usage:
        # Creation
        salary = Money(Decimal("1500.00"), Currency.USD)
        salary = Money.usd(1500)  # Convenience method
        salary = Money.zig(25000)

        # Arithmetic
        total = salary.add(bonus)
        net = gross.subtract(deduction)
        tax = gross.multiply(Decimal("0.25"))

        # Comparison
        if salary.is_greater_than(minimum_wage):
            ...
    """

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        """Validate money on creation."""
        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        # Ensure currency is Currency enum
        if isinstance(self.currency, str):
            object.__setattr__(self, "currency", Currency(self.currency))

    @classmethod
    def usd(cls, amount: Decimal | float | int | str) -> "Money":
        """Create Money in USD."""
        return cls(amount=Decimal(str(amount)), currency=Currency.USD)

    @classmethod
    def zig(cls, amount: Decimal | float | int | str) -> "Money":
        """Create Money in ZIG."""
        return cls(amount=Decimal(str(amount)), currency=Currency.ZIG)

    @classmethod
    def zero(cls, currency: Currency) -> "Money":
        """Create zero amount in specified currency."""
        return cls(amount=Decimal("0"), currency=currency)

    def add(self, other: "Money") -> "Money":
        """
        Add two Money amounts.

        Raises:
            ValidationError: If currencies don't match
        """
        self._validate_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        """
        Subtract Money amount.

        Raises:
            ValidationError: If currencies don't match
        """
        self._validate_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: Decimal | float | int) -> "Money":
        """Multiply by a factor (e.g., tax rate)."""
        return Money(
            amount=self.amount * Decimal(str(factor)),
            currency=self.currency,
        )

    def divide(self, divisor: Decimal | float | int) -> "Money":
        """
        Divide by a divisor.

        Raises:
            ValidationError: If divisor is zero
        """
        if Decimal(str(divisor)) == 0:
            raise ValidationError("Cannot divide by zero", code="DIVISION_BY_ZERO")
        return Money(
            amount=self.amount / Decimal(str(divisor)),
            currency=self.currency,
        )

    def round(self, decimal_places: int = 2) -> "Money":
        """Round to specified decimal places (default 2)."""
        quantize_str = "0." + "0" * decimal_places
        return Money(
            amount=self.amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP),
            currency=self.currency,
        )

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_greater_than(self, other: "Money") -> bool:
        """Check if this amount is greater than other."""
        self._validate_same_currency(other)
        return self.amount > other.amount

    def is_less_than(self, other: "Money") -> bool:
        """Check if this amount is less than other."""
        self._validate_same_currency(other)
        return self.amount < other.amount

    def is_greater_or_equal(self, other: "Money") -> bool:
        """Check if this amount is greater than or equal to other."""
        self._validate_same_currency(other)
        return self.amount >= other.amount

    def is_less_or_equal(self, other: "Money") -> bool:
        """Check if this amount is less than or equal to other."""
        self._validate_same_currency(other)
        return self.amount <= other.amount

    def negate(self) -> "Money":
        """Return the negation of this amount."""
        return Money(amount=-self.amount, currency=self.currency)

    def abs(self) -> "Money":
        """Return absolute value."""
        return Money(amount=abs(self.amount), currency=self.currency)

    def _validate_same_currency(self, other: "Money") -> None:
        """Validate that both Money objects have the same currency."""
        if self.currency != other.currency:
            raise ValidationError(
                f"Cannot operate on different currencies: {self.currency} and {other.currency}",
                code="CURRENCY_MISMATCH",
                details={"currency1": str(self.currency), "currency2": str(other.currency)},
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "amount": str(self.amount),
            "currency": str(self.currency),
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.currency} {self.amount:,.2f}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"

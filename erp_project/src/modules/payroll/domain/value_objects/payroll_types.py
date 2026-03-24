"""
Payroll value objects and enums.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.domain.base import ValueObject


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    ZIG = "ZIG"

    @classmethod
    def from_string(cls, value: str) -> "Currency":
        """Create currency from string."""
        normalized = value.upper().strip()
        for currency in cls:
            if currency.value == normalized:
                return currency
        raise ValueError(f"Invalid currency: {value}")


class PayrollStatus(str, Enum):
    """Status of a payroll batch."""

    OPEN = "Open"
    PROCESSING = "Processing"
    CLOSED = "Closed"

    @property
    def can_process(self) -> bool:
        """Check if payroll can be processed."""
        return self == PayrollStatus.OPEN

    @property
    def can_reopen(self) -> bool:
        """Check if payroll can be reopened."""
        return self == PayrollStatus.CLOSED

    @classmethod
    def from_string(cls, value: str) -> "PayrollStatus":
        """Create status from string."""
        normalized = value.strip().title()
        for status in cls:
            if status.value == normalized:
                return status
        raise ValueError(f"Invalid payroll status: {value}")


class PayslipStatus(str, Enum):
    """Status of an individual payslip."""

    DRAFT = "Draft"
    PENDING = "Pending"
    PROCESSED = "Processed"
    FAILED = "Failed"
    PAID = "Paid"

    @property
    def is_final(self) -> bool:
        """Check if this is a final status."""
        return self in (PayslipStatus.PROCESSED, PayslipStatus.PAID)

    @property
    def can_edit(self) -> bool:
        """Check if payslip can be edited."""
        return self == PayslipStatus.DRAFT

    @property
    def can_approve(self) -> bool:
        """Check if payslip can be approved."""
        return self == PayslipStatus.DRAFT

    @classmethod
    def from_string(cls, value: str) -> "PayslipStatus":
        """Create status from string."""
        normalized = value.strip().title()
        for status in cls:
            if status.value == normalized:
                return status
        raise ValueError(f"Invalid payslip status: {value}")


@dataclass(frozen=True)
class PayrollPeriod(ValueObject):
    """
    Represents a payroll period (year and month).

    Immutable value object for payroll period identification.
    """

    year: int
    month: int

    def __post_init__(self) -> None:
        """Validate period values."""
        if not 1900 <= self.year <= 2100:
            raise ValueError(f"Invalid year: {self.year}")
        if not 1 <= self.month <= 12:
            raise ValueError(f"Invalid month: {self.month}")

    @property
    def display(self) -> str:
        """Human-readable format: 'January 2025'."""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{months[self.month - 1]} {self.year}"

    @property
    def code(self) -> str:
        """Short code format: '2025-01'."""
        return f"{self.year}-{self.month:02d}"

    @classmethod
    def from_string(cls, value: str) -> "PayrollPeriod":
        """
        Create period from string format 'YYYY-MM'.

        Args:
            value: String in format 'YYYY-MM'

        Returns:
            PayrollPeriod instance
        """
        parts = value.strip().split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid period format: {value}. Expected YYYY-MM")
        return cls(year=int(parts[0]), month=int(parts[1]))

    def next(self) -> "PayrollPeriod":
        """Get the next period."""
        if self.month == 12:
            return PayrollPeriod(year=self.year + 1, month=1)
        return PayrollPeriod(year=self.year, month=self.month + 1)

    def previous(self) -> "PayrollPeriod":
        """Get the previous period."""
        if self.month == 1:
            return PayrollPeriod(year=self.year - 1, month=12)
        return PayrollPeriod(year=self.year, month=self.month - 1)


@dataclass(frozen=True)
class TaxBracket(ValueObject):
    """
    Represents a tax bracket for PAYE calculation.

    Formula: tax = (income * rate) - deduction
    """

    min_income: Decimal
    max_income: Optional[Decimal]  # None for highest bracket
    rate: Decimal
    deduction: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        """Validate bracket values."""
        if self.min_income < 0:
            raise ValueError("Minimum income cannot be negative")
        if self.max_income is not None and self.max_income < self.min_income:
            raise ValueError("Maximum income cannot be less than minimum")
        if not (Decimal("0") <= self.rate <= Decimal("1")):
            raise ValueError("Rate must be between 0 and 1")
        if self.deduction < 0:
            raise ValueError("Deduction cannot be negative")

    def applies_to(self, income: Decimal) -> bool:
        """Check if this bracket applies to the given income."""
        if income < self.min_income:
            return False
        if self.max_income is not None and income >= self.max_income:
            return False
        return True

    def calculate_tax(self, income: Decimal) -> Decimal:
        """Calculate tax for this bracket."""
        tax = (income * self.rate) - self.deduction
        return max(Decimal("0"), tax)

    @property
    def display(self) -> str:
        """Human-readable format."""
        max_str = "and above" if self.max_income is None else f"- {self.max_income:,.2f}"
        rate_pct = self.rate * 100
        return f"{self.currency.value} {self.min_income:,.2f} {max_str}: {rate_pct:.1f}%"

"""
Accounting value objects and enums.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.domain.base import ValueObject


class AccountType(str, Enum):
    """Types of accounts in the chart of accounts."""

    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    VIEW = "View"  # Non-posting parent accounts
    CONSOLIDATION = "Consolidation"

    @property
    def is_posting(self) -> bool:
        """Check if this account type allows posting."""
        return self not in (AccountType.VIEW, AccountType.CONSOLIDATION)

    @property
    def normal_balance(self) -> str:
        """Get the normal balance side for this account type."""
        if self in (AccountType.ASSET, AccountType.EXPENSE):
            return "debit"
        return "credit"

    @classmethod
    def from_string(cls, value: str) -> "AccountType":
        """Create account type from string."""
        normalized = value.strip().title()
        for acc_type in cls:
            if acc_type.value == normalized:
                return acc_type
        raise ValueError(f"Invalid account type: {value}")


class JournalType(str, Enum):
    """Types of journals."""

    SALE = "Sale"
    PURCHASE = "Purchase"
    CASH = "Cash"
    BANK = "Bank"
    GENERAL = "General"

    @classmethod
    def from_string(cls, value: str) -> "JournalType":
        """Create journal type from string."""
        normalized = value.strip().title()
        for j_type in cls:
            if j_type.value == normalized:
                return j_type
        raise ValueError(f"Invalid journal type: {value}")


class PartnerType(str, Enum):
    """Types of partners."""

    CUSTOMER = "Customer"
    SUPPLIER = "Supplier"
    EMPLOYEE = "Employee"

    @classmethod
    def from_string(cls, value: str) -> "PartnerType":
        """Create partner type from string."""
        normalized = value.strip().title()
        for p_type in cls:
            if p_type.value == normalized:
                return p_type
        raise ValueError(f"Invalid partner type: {value}")


@dataclass(frozen=True)
class AccountCode(ValueObject):
    """Value object representing an account code."""

    value: str

    def __post_init__(self) -> None:
        """Validate account code."""
        if not self.value or not self.value.strip():
            raise ValueError("Account code cannot be empty")

    @property
    def category_prefix(self) -> str:
        """Get the first digit (category prefix)."""
        return self.value[0] if self.value else ""

    @property
    def is_asset(self) -> bool:
        """Check if this is an asset account (starts with 1)."""
        return self.category_prefix == "1"

    @property
    def is_liability(self) -> bool:
        """Check if this is a liability account (starts with 2)."""
        return self.category_prefix == "2"

    @property
    def is_equity(self) -> bool:
        """Check if this is an equity account (starts with 3)."""
        return self.category_prefix == "3"

    @property
    def is_revenue(self) -> bool:
        """Check if this is a revenue account (starts with 4)."""
        return self.category_prefix == "4"

    @property
    def is_expense(self) -> bool:
        """Check if this is an expense account (starts with 5)."""
        return self.category_prefix == "5"


@dataclass(frozen=True)
class Money(ValueObject):
    """Value object representing a monetary amount with currency."""

    amount: Decimal
    currency_code: str

    def __post_init__(self) -> None:
        """Validate money."""
        if not self.currency_code:
            raise ValueError("Currency code is required")

    def add(self, other: "Money") -> "Money":
        """Add two money amounts."""
        if self.currency_code != other.currency_code:
            raise ValueError("Cannot add different currencies")
        return Money(
            amount=self.amount + other.amount,
            currency_code=self.currency_code
        )

    def subtract(self, other: "Money") -> "Money":
        """Subtract two money amounts."""
        if self.currency_code != other.currency_code:
            raise ValueError("Cannot subtract different currencies")
        return Money(
            amount=self.amount - other.amount,
            currency_code=self.currency_code
        )

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0")

    @property
    def display(self) -> str:
        """Get display format."""
        return f"{self.currency_code} {self.amount:,.2f}"


@dataclass(frozen=True)
class DebitCredit(ValueObject):
    """Value object representing a debit/credit entry."""

    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate debit/credit."""
        if self.debit < 0:
            raise ValueError("Debit cannot be negative")
        if self.credit < 0:
            raise ValueError("Credit cannot be negative")

    @property
    def balance(self) -> Decimal:
        """Get the balance (debit - credit)."""
        return self.debit - self.credit

    @property
    def is_balanced(self) -> bool:
        """Check if debit equals credit."""
        return self.debit == self.credit

    def add(self, other: "DebitCredit") -> "DebitCredit":
        """Add two debit/credit entries."""
        return DebitCredit(
            debit=self.debit + other.debit,
            credit=self.credit + other.credit
        )

"""
Employment-related value objects.
"""

from dataclasses import dataclass
from enum import Enum

from shared.domain.base import ValueObject


class EmploymentType(str, Enum):
    """Type of employment contract."""

    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERN = "Intern"

    @classmethod
    def from_string(cls, value: str) -> "EmploymentType":
        """Convert string to EmploymentType."""
        value_lower = value.lower().replace("-", "").replace("_", "").replace(" ", "")
        mapping = {
            "fulltime": cls.FULL_TIME,
            "parttime": cls.PART_TIME,
            "contract": cls.CONTRACT,
            "intern": cls.INTERN,
        }
        if value_lower in mapping:
            return mapping[value_lower]
        raise ValueError(f"Invalid employment type: {value}")


class PayFrequency(str, Enum):
    """How often an employee is paid."""

    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    BI_WEEKLY = "Bi-Weekly"

    @classmethod
    def from_string(cls, value: str) -> "PayFrequency":
        """Convert string to PayFrequency."""
        value_lower = value.lower().replace("-", "").replace("_", "").replace(" ", "")
        mapping = {
            "monthly": cls.MONTHLY,
            "weekly": cls.WEEKLY,
            "biweekly": cls.BI_WEEKLY,
        }
        if value_lower in mapping:
            return mapping[value_lower]
        raise ValueError(f"Invalid pay frequency: {value}")


class Gender(str, Enum):
    """Employee gender."""

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

    @classmethod
    def from_string(cls, value: str) -> "Gender":
        """Convert string to Gender."""
        value_lower = value.lower()
        mapping = {
            "male": cls.MALE,
            "m": cls.MALE,
            "female": cls.FEMALE,
            "f": cls.FEMALE,
            "other": cls.OTHER,
        }
        if value_lower in mapping:
            return mapping[value_lower]
        raise ValueError(f"Invalid gender: {value}")


class MaritalStatus(str, Enum):
    """Employee marital status."""

    SINGLE = "Single"
    MARRIED = "Married"
    DIVORCED = "Divorced"
    WIDOWED = "Widowed"

    @classmethod
    def from_string(cls, value: str) -> "MaritalStatus":
        """Convert string to MaritalStatus."""
        value_lower = value.lower()
        mapping = {
            "single": cls.SINGLE,
            "married": cls.MARRIED,
            "divorced": cls.DIVORCED,
            "widowed": cls.WIDOWED,
        }
        if value_lower in mapping:
            return mapping[value_lower]
        raise ValueError(f"Invalid marital status: {value}")


@dataclass(frozen=True)
class BankAccount(ValueObject):
    """
    Bank account information.

    Attributes:
        bank_name: Name of the bank
        account_number: Account number
    """

    bank_name: str
    account_number: str

    def __post_init__(self):
        """Validate bank account."""
        if self.bank_name and not self.account_number:
            raise ValueError("Account number is required when bank name is provided")
        if self.account_number and not self.bank_name:
            raise ValueError("Bank name is required when account number is provided")

    @classmethod
    def empty(cls) -> "BankAccount":
        """Create an empty bank account."""
        return cls(bank_name="", account_number="")

    @property
    def is_empty(self) -> bool:
        """Check if the bank account is empty."""
        return not self.bank_name and not self.account_number

    def __str__(self) -> str:
        """String representation."""
        if self.is_empty:
            return "No bank account"
        return f"{self.bank_name}: {self.account_number}"

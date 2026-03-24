"""
Leave value objects.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from shared.domain.base import ValueObject
from shared.domain.exceptions import ValidationError


class LeaveStatus(str, Enum):
    """Leave request status types."""

    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"

    @classmethod
    def from_string(cls, value: str) -> "LeaveStatus":
        """Create status from string."""
        normalized = value.lower()
        for status in cls:
            if status.value.lower() == normalized:
                return status
        raise ValueError(f"Invalid leave status: {value}")

    @property
    def is_final(self) -> bool:
        """Check if status is final (cannot be changed)."""
        return self in (LeaveStatus.APPROVED, LeaveStatus.REJECTED, LeaveStatus.CANCELLED)

    @property
    def can_cancel(self) -> bool:
        """Check if leave can be cancelled from this status."""
        return self == LeaveStatus.PENDING


@dataclass(frozen=True)
class LeavePeriod(ValueObject):
    """
    Leave period value object.

    Represents a period of leave with start and end dates.
    """

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Validate leave period."""
        if self.end_date < self.start_date:
            raise ValidationError(
                message="End date cannot be before start date",
                code="INVALID_DATE_RANGE",
            )

    @property
    def days(self) -> int:
        """Calculate number of days in the period (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    @property
    def business_days(self) -> int:
        """
        Calculate business days (excluding weekends).

        Note: Does not account for holidays.
        """
        total = 0
        current = self.start_date
        while current <= self.end_date:
            # Monday is 0, Sunday is 6
            if current.weekday() < 5:
                total += 1
            current = date(
                current.year,
                current.month,
                current.day + 1 if current.day < 28 else 1,
            )
            # Handle month rollover properly
            from datetime import timedelta
            current = self.start_date + timedelta(days=(current - self.start_date).days + 1)
            if current > self.end_date:
                break
        return total

    def overlaps_with(self, other: "LeavePeriod") -> bool:
        """Check if this period overlaps with another."""
        return self.start_date <= other.end_date and self.end_date >= other.start_date

    def contains(self, check_date: date) -> bool:
        """Check if a date falls within this period."""
        return self.start_date <= check_date <= self.end_date

    @classmethod
    def create(cls, start_date: date, end_date: date) -> "LeavePeriod":
        """Create a leave period."""
        return cls(start_date=start_date, end_date=end_date)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.start_date} to {self.end_date} ({self.days} days)"


@dataclass(frozen=True)
class LeaveEntitlement(ValueObject):
    """
    Leave entitlement value object.

    Represents an employee's leave entitlement for a specific type.
    """

    entitled_days: Decimal
    used_days: Decimal

    def __post_init__(self) -> None:
        """Validate entitlement."""
        if self.entitled_days < 0:
            raise ValidationError(
                message="Entitled days cannot be negative",
                code="NEGATIVE_ENTITLEMENT",
            )
        if self.used_days < 0:
            raise ValidationError(
                message="Used days cannot be negative",
                code="NEGATIVE_USED_DAYS",
            )

    @property
    def remaining_days(self) -> Decimal:
        """Calculate remaining days."""
        return self.entitled_days - self.used_days

    @property
    def is_exhausted(self) -> bool:
        """Check if entitlement is exhausted."""
        return self.remaining_days <= 0

    @property
    def usage_percentage(self) -> Decimal:
        """Calculate percentage of entitlement used."""
        if self.entitled_days == 0:
            return Decimal("0")
        return (self.used_days / self.entitled_days) * 100

    def can_take(self, days: Decimal) -> bool:
        """Check if employee can take specified number of days."""
        return self.remaining_days >= days

    def with_usage(self, additional_days: Decimal) -> "LeaveEntitlement":
        """Create new entitlement with additional usage."""
        new_used = self.used_days + additional_days
        if new_used > self.entitled_days:
            raise ValidationError(
                message=f"Cannot use {additional_days} days. Only {self.remaining_days} remaining.",
                code="INSUFFICIENT_BALANCE",
            )
        return LeaveEntitlement(
            entitled_days=self.entitled_days,
            used_days=new_used,
        )

    def with_reversal(self, days: Decimal) -> "LeaveEntitlement":
        """Create new entitlement with usage reversed (e.g., cancelled leave)."""
        new_used = self.used_days - days
        if new_used < 0:
            new_used = Decimal("0")
        return LeaveEntitlement(
            entitled_days=self.entitled_days,
            used_days=new_used,
        )

    @classmethod
    def create(cls, entitled_days: int | Decimal, used_days: int | Decimal = 0) -> "LeaveEntitlement":
        """Create a leave entitlement."""
        return cls(
            entitled_days=Decimal(str(entitled_days)),
            used_days=Decimal(str(used_days)),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.remaining_days}/{self.entitled_days} days remaining"

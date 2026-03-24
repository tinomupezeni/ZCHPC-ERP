"""
Period value object for payroll and reporting periods.

Represents a year-month combination used throughout the ERP
for payroll processing, reporting, and historical data.

Example:
    current = Period(2026, 3)
    previous = current.previous()  # Period(2026, 2)
    date_range = current.to_date_range()
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError
from shared.domain.value_objects.date_range import DateRange


@dataclass(frozen=True)
class Period(ValueObject):
    """
    Value object representing a year-month period.

    Used for payroll processing, reporting periods, and any
    month-based calculations throughout the ERP system.

    Attributes:
        year: The year (e.g., 2026)
        month: The month (1-12)

    Usage:
        # Creation
        period = Period(2026, 3)  # March 2026
        period = Period.current()  # Current month
        period = Period.from_date(some_date)

        # Navigation
        next_month = period.next()
        prev_month = period.previous()

        # Conversion
        date_range = period.to_date_range()
        start = period.first_day
        end = period.last_day
    """

    year: int
    month: int

    def __post_init__(self) -> None:
        """Validate period on creation."""
        if not 1 <= self.month <= 12:
            raise ValidationError(
                f"Month must be between 1 and 12, got {self.month}",
                code="INVALID_MONTH",
                details={"month": self.month},
            )
        if self.year < 1900 or self.year > 2100:
            raise ValidationError(
                f"Year must be between 1900 and 2100, got {self.year}",
                code="INVALID_YEAR",
                details={"year": self.year},
            )

    @classmethod
    def current(cls) -> "Period":
        """Create a Period for the current month."""
        today = date.today()
        return cls(year=today.year, month=today.month)

    @classmethod
    def from_date(cls, d: date) -> "Period":
        """Create a Period from a date."""
        return cls(year=d.year, month=d.month)

    @classmethod
    def from_string(cls, period_str: str) -> "Period":
        """
        Parse period from string format YYYY-MM.

        Args:
            period_str: String in format "2026-03"

        Raises:
            ValidationError: If string format is invalid
        """
        try:
            parts = period_str.split("-")
            if len(parts) != 2:
                raise ValueError("Invalid format")
            return cls(year=int(parts[0]), month=int(parts[1]))
        except (ValueError, IndexError) as e:
            raise ValidationError(
                f"Invalid period format: {period_str}. Expected YYYY-MM",
                code="INVALID_PERIOD_FORMAT",
                details={"input": period_str},
            ) from e

    @property
    def first_day(self) -> date:
        """First day of the period."""
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        """Last day of the period."""
        if self.month == 12:
            return date(self.year + 1, 1, 1) - __import__("datetime").timedelta(days=1)
        return date(self.year, self.month + 1, 1) - __import__("datetime").timedelta(days=1)

    @property
    def days_in_month(self) -> int:
        """Number of days in this period's month."""
        return (self.last_day - self.first_day).days + 1

    def next(self) -> "Period":
        """Get the next period (following month)."""
        if self.month == 12:
            return Period(year=self.year + 1, month=1)
        return Period(year=self.year, month=self.month + 1)

    def previous(self) -> "Period":
        """Get the previous period (preceding month)."""
        if self.month == 1:
            return Period(year=self.year - 1, month=12)
        return Period(year=self.year, month=self.month - 1)

    def add_months(self, months: int) -> "Period":
        """
        Add (or subtract) months from this period.

        Args:
            months: Number of months to add (negative to subtract)
        """
        total_months = self.year * 12 + self.month - 1 + months
        new_year = total_months // 12
        new_month = total_months % 12 + 1
        return Period(year=new_year, month=new_month)

    def to_date_range(self) -> DateRange:
        """Convert to a DateRange covering the full month."""
        return DateRange(start_date=self.first_day, end_date=self.last_day)

    def contains(self, d: date) -> bool:
        """Check if a date falls within this period."""
        return d.year == self.year and d.month == self.month

    def is_before(self, other: "Period") -> bool:
        """Check if this period is before another."""
        return (self.year, self.month) < (other.year, other.month)

    def is_after(self, other: "Period") -> bool:
        """Check if this period is after another."""
        return (self.year, self.month) > (other.year, other.month)

    def months_between(self, other: "Period") -> int:
        """
        Calculate months between this period and another.

        Returns positive if other is after this, negative if before.
        """
        return (other.year - self.year) * 12 + (other.month - self.month)

    @staticmethod
    def range(start: "Period", end: "Period") -> list["Period"]:
        """
        Generate list of periods from start to end (inclusive).

        Args:
            start: First period
            end: Last period

        Returns:
            List of all periods from start to end
        """
        if start.is_after(end):
            return []

        periods = []
        current = start
        while not current.is_after(end):
            periods.append(current)
            current = current.next()
        return periods

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "year": self.year,
            "month": self.month,
            "period": str(self),
        }

    def __str__(self) -> str:
        """String representation in YYYY-MM format."""
        return f"{self.year}-{self.month:02d}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Period(year={self.year}, month={self.month})"

    def __lt__(self, other: "Period") -> bool:
        """Less than comparison for sorting."""
        return self.is_before(other)

    def __le__(self, other: "Period") -> bool:
        """Less than or equal comparison."""
        return self == other or self.is_before(other)

    def __gt__(self, other: "Period") -> bool:
        """Greater than comparison."""
        return self.is_after(other)

    def __ge__(self, other: "Period") -> bool:
        """Greater than or equal comparison."""
        return self == other or self.is_after(other)

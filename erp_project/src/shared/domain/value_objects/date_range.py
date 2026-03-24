"""
DateRange value object for date periods.

Handles date ranges with validation and useful operations
like calculating duration, checking overlaps, and containment.

Example:
    leave_period = DateRange(date(2026, 3, 1), date(2026, 3, 10))
    days = leave_period.days  # 10
    if leave_period.contains(date(2026, 3, 5)):
        ...
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterator

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


@dataclass(frozen=True)
class DateRange(ValueObject):
    """
    Value object representing a range of dates (inclusive).

    Both start_date and end_date are included in the range.
    DateRange is immutable and operations return new instances.

    Attributes:
        start_date: First day of the range (inclusive)
        end_date: Last day of the range (inclusive)

    Usage:
        # Creation
        period = DateRange(date(2026, 3, 1), date(2026, 3, 31))
        period = DateRange.month(2026, 3)  # Convenience for full month
        period = DateRange.single_day(date(2026, 3, 15))

        # Properties
        days = period.days  # Number of days
        dates = list(period)  # Iterate all dates

        # Operations
        if period.contains(some_date):
            ...
        if period.overlaps(other_period):
            ...
    """

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        """Validate date range on creation."""
        if self.start_date > self.end_date:
            raise ValidationError(
                f"Start date ({self.start_date}) cannot be after end date ({self.end_date})",
                code="INVALID_DATE_RANGE",
                details={"start_date": str(self.start_date), "end_date": str(self.end_date)},
            )

    @classmethod
    def single_day(cls, day: date) -> "DateRange":
        """Create a range for a single day."""
        return cls(start_date=day, end_date=day)

    @classmethod
    def month(cls, year: int, month: int) -> "DateRange":
        """Create a range for a full calendar month."""
        start = date(year, month, 1)
        # Find last day of month
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return cls(start_date=start, end_date=end)

    @classmethod
    def year(cls, year: int) -> "DateRange":
        """Create a range for a full calendar year."""
        return cls(start_date=date(year, 1, 1), end_date=date(year, 12, 31))

    @property
    def days(self) -> int:
        """Number of days in the range (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    def contains(self, day: date) -> bool:
        """Check if a date falls within this range."""
        return self.start_date <= day <= self.end_date

    def contains_range(self, other: "DateRange") -> bool:
        """Check if another range is fully contained within this range."""
        return self.start_date <= other.start_date and self.end_date >= other.end_date

    def overlaps(self, other: "DateRange") -> bool:
        """Check if this range overlaps with another range."""
        return self.start_date <= other.end_date and self.end_date >= other.start_date

    def intersection(self, other: "DateRange") -> "DateRange | None":
        """
        Get the overlapping portion of two ranges.

        Returns:
            DateRange of the overlap, or None if no overlap
        """
        if not self.overlaps(other):
            return None
        return DateRange(
            start_date=max(self.start_date, other.start_date),
            end_date=min(self.end_date, other.end_date),
        )

    def extend(self, days: int) -> "DateRange":
        """
        Extend the range by the specified number of days.

        Positive days extend the end, negative days extend the start.
        """
        if days >= 0:
            return DateRange(start_date=self.start_date, end_date=self.end_date + timedelta(days=days))
        else:
            return DateRange(start_date=self.start_date + timedelta(days=days), end_date=self.end_date)

    def shift(self, days: int) -> "DateRange":
        """Shift the entire range by the specified number of days."""
        delta = timedelta(days=days)
        return DateRange(start_date=self.start_date + delta, end_date=self.end_date + delta)

    def split_by_month(self) -> list["DateRange"]:
        """Split a range into separate ranges for each calendar month."""
        ranges = []
        current_start = self.start_date

        while current_start <= self.end_date:
            # Find end of current month
            if current_start.month == 12:
                month_end = date(current_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(current_start.year, current_start.month + 1, 1) - timedelta(days=1)

            # Use the earlier of month_end or self.end_date
            range_end = min(month_end, self.end_date)
            ranges.append(DateRange(start_date=current_start, end_date=range_end))

            # Move to first day of next month
            current_start = range_end + timedelta(days=1)

        return ranges

    def __iter__(self) -> Iterator[date]:
        """Iterate over all dates in the range."""
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)

    def __len__(self) -> int:
        """Number of days in the range."""
        return self.days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "days": self.days,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.start_date} to {self.end_date} ({self.days} days)"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"DateRange(start_date={self.start_date!r}, end_date={self.end_date!r})"

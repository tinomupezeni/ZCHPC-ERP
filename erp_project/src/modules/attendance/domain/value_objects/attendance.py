"""
Attendance value objects.
"""

from dataclasses import dataclass
from datetime import time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.domain.base import ValueObject


class AttendanceStatus(str, Enum):
    """Attendance status types."""

    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    HALF_DAY = "Half Day"
    ON_LEAVE = "On Leave"
    WEEKEND = "Weekend"
    HOLIDAY = "Holiday"

    @classmethod
    def from_string(cls, value: str) -> "AttendanceStatus":
        """Create status from string."""
        normalized = value.lower().replace(" ", "_").replace("-", "_")
        for status in cls:
            if status.value.lower().replace(" ", "_") == normalized:
                return status
        raise ValueError(f"Invalid attendance status: {value}")


@dataclass(frozen=True)
class ClockTime(ValueObject):
    """
    Clock time value object.

    Represents a clock-in or clock-out time with validation.
    """

    hour: int
    minute: int
    second: int = 0

    def __post_init__(self) -> None:
        """Validate clock time."""
        if not (0 <= self.hour <= 23):
            raise ValueError(f"Hour must be between 0 and 23, got {self.hour}")
        if not (0 <= self.minute <= 59):
            raise ValueError(f"Minute must be between 0 and 59, got {self.minute}")
        if not (0 <= self.second <= 59):
            raise ValueError(f"Second must be between 0 and 59, got {self.second}")

    @classmethod
    def from_time(cls, t: time) -> "ClockTime":
        """Create from Python time object."""
        return cls(hour=t.hour, minute=t.minute, second=t.second)

    @classmethod
    def from_string(cls, value: str) -> "ClockTime":
        """Create from HH:MM or HH:MM:SS string."""
        parts = value.split(":")
        if len(parts) == 2:
            return cls(hour=int(parts[0]), minute=int(parts[1]))
        elif len(parts) == 3:
            return cls(hour=int(parts[0]), minute=int(parts[1]), second=int(parts[2]))
        raise ValueError(f"Invalid time format: {value}")

    def to_time(self) -> time:
        """Convert to Python time object."""
        return time(hour=self.hour, minute=self.minute, second=self.second)

    def to_minutes(self) -> int:
        """Convert to total minutes from midnight."""
        return self.hour * 60 + self.minute

    def __str__(self) -> str:
        """String representation."""
        return f"{self.hour:02d}:{self.minute:02d}"


@dataclass(frozen=True)
class WorkDuration(ValueObject):
    """
    Work duration value object.

    Represents the duration of work in hours and minutes.
    """

    hours: int
    minutes: int

    def __post_init__(self) -> None:
        """Validate work duration."""
        if self.hours < 0:
            raise ValueError(f"Hours cannot be negative, got {self.hours}")
        if not (0 <= self.minutes <= 59):
            raise ValueError(f"Minutes must be between 0 and 59, got {self.minutes}")

    @classmethod
    def from_clock_times(
        cls, time_in: ClockTime, time_out: ClockTime
    ) -> "WorkDuration":
        """Calculate duration between two clock times."""
        in_minutes = time_in.to_minutes()
        out_minutes = time_out.to_minutes()

        # Handle overnight shifts (clock out after midnight)
        if out_minutes < in_minutes:
            out_minutes += 24 * 60

        total_minutes = out_minutes - in_minutes
        return cls(hours=total_minutes // 60, minutes=total_minutes % 60)

    @classmethod
    def zero(cls) -> "WorkDuration":
        """Create zero duration."""
        return cls(hours=0, minutes=0)

    @property
    def total_minutes(self) -> int:
        """Get total duration in minutes."""
        return self.hours * 60 + self.minutes

    @property
    def total_hours(self) -> Decimal:
        """Get total duration in decimal hours."""
        return Decimal(str(self.total_minutes)) / Decimal("60")

    def __add__(self, other: "WorkDuration") -> "WorkDuration":
        """Add two durations."""
        total = self.total_minutes + other.total_minutes
        return WorkDuration(hours=total // 60, minutes=total % 60)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.hours}h {self.minutes}m"


@dataclass(frozen=True)
class AttendanceSummary(ValueObject):
    """
    Attendance summary for a period.

    Contains aggregate statistics for an employee's attendance.
    """

    days_present: int
    days_absent: int
    days_late: int
    days_half_day: int
    days_on_leave: int
    total_hours_worked: Decimal
    average_hours_per_day: Decimal

    @property
    def total_working_days(self) -> int:
        """Get total working days (excluding weekends/holidays)."""
        return (
            self.days_present
            + self.days_absent
            + self.days_late
            + self.days_half_day
            + self.days_on_leave
        )

    @property
    def attendance_rate(self) -> Decimal:
        """Calculate attendance rate as percentage."""
        if self.total_working_days == 0:
            return Decimal("0")
        present_days = self.days_present + self.days_late + self.days_half_day
        return (Decimal(str(present_days)) / Decimal(str(self.total_working_days))) * 100

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Present: {self.days_present}, "
            f"Absent: {self.days_absent}, "
            f"Late: {self.days_late}, "
            f"Hours: {self.total_hours_worked:.2f}"
        )

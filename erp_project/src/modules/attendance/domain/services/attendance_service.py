"""
Attendance domain services.
"""

from abc import ABC, abstractmethod
from datetime import date, time
from decimal import Decimal
from typing import Sequence

from modules.attendance.domain.entities import AttendanceRecord
from modules.attendance.domain.value_objects import (
    AttendanceStatus,
    AttendanceSummary,
    ClockTime,
    WorkDuration,
)


class ILateArrivalDetector(ABC):
    """Interface for detecting late arrivals."""

    @abstractmethod
    def is_late(self, clock_in_time: ClockTime) -> bool:
        """
        Check if a clock-in time is considered late.

        Args:
            clock_in_time: The clock-in time to check

        Returns:
            True if the employee is late
        """
        ...

    @abstractmethod
    def minutes_late(self, clock_in_time: ClockTime) -> int:
        """
        Calculate how many minutes late the employee is.

        Args:
            clock_in_time: The clock-in time to check

        Returns:
            Number of minutes late (0 if not late)
        """
        ...


class LateArrivalDetector(ILateArrivalDetector):
    """
    Default late arrival detector.

    Detects late arrivals based on standard work start time and grace period.
    """

    def __init__(
        self,
        work_start_time: time = time(8, 0),
        grace_period_minutes: int = 15,
    ):
        """
        Initialize detector.

        Args:
            work_start_time: Expected work start time
            grace_period_minutes: Grace period before marking as late
        """
        self.work_start_time = work_start_time
        self.grace_period_minutes = grace_period_minutes
        self._start_minutes = work_start_time.hour * 60 + work_start_time.minute

    def is_late(self, clock_in_time: ClockTime) -> bool:
        """Check if clock-in time is late."""
        return self.minutes_late(clock_in_time) > 0

    def minutes_late(self, clock_in_time: ClockTime) -> int:
        """Calculate minutes late."""
        clock_in_minutes = clock_in_time.to_minutes()
        late_by = clock_in_minutes - self._start_minutes - self.grace_period_minutes

        return max(0, late_by)


class IAttendanceSummaryCalculator(ABC):
    """Interface for calculating attendance summaries."""

    @abstractmethod
    def calculate(self, records: Sequence[AttendanceRecord]) -> AttendanceSummary:
        """
        Calculate attendance summary from records.

        Args:
            records: List of attendance records

        Returns:
            AttendanceSummary with aggregate statistics
        """
        ...


class AttendanceSummaryCalculator(IAttendanceSummaryCalculator):
    """
    Default attendance summary calculator.

    Aggregates attendance records into summary statistics.
    """

    def __init__(self, late_detector: ILateArrivalDetector | None = None):
        """
        Initialize calculator.

        Args:
            late_detector: Late arrival detector (uses default if not provided)
        """
        self.late_detector = late_detector or LateArrivalDetector()

    def calculate(self, records: Sequence[AttendanceRecord]) -> AttendanceSummary:
        """Calculate attendance summary from records."""
        days_present = 0
        days_absent = 0
        days_late = 0
        days_half_day = 0
        total_duration = WorkDuration.zero()

        for record in records:
            status = record.status

            if status == AttendanceStatus.PRESENT:
                days_present += 1
            elif status == AttendanceStatus.ABSENT:
                days_absent += 1
            elif status == AttendanceStatus.LATE:
                days_late += 1
            elif status == AttendanceStatus.HALF_DAY:
                days_half_day += 1

            if record.is_complete:
                total_duration = total_duration + record.work_duration

        total_hours = total_duration.total_hours
        working_days = days_present + days_late + days_half_day

        if working_days > 0:
            avg_hours = total_hours / Decimal(str(working_days))
        else:
            avg_hours = Decimal("0")

        return AttendanceSummary(
            days_present=days_present,
            days_absent=days_absent,
            days_late=days_late,
            days_half_day=days_half_day,
            days_on_leave=0,  # To be filled by leave module integration
            total_hours_worked=total_hours,
            average_hours_per_day=avg_hours.quantize(Decimal("0.01")),
        )


class IWorkScheduleChecker(ABC):
    """Interface for checking work schedules."""

    @abstractmethod
    def is_working_day(self, check_date: date) -> bool:
        """
        Check if a date is a working day.

        Args:
            check_date: The date to check

        Returns:
            True if it's a working day
        """
        ...

    @abstractmethod
    def is_holiday(self, check_date: date) -> bool:
        """
        Check if a date is a holiday.

        Args:
            check_date: The date to check

        Returns:
            True if it's a holiday
        """
        ...


class DefaultWorkScheduleChecker(IWorkScheduleChecker):
    """
    Default work schedule checker.

    Considers Monday-Friday as working days.
    """

    def __init__(self, holidays: set[date] | None = None):
        """
        Initialize checker.

        Args:
            holidays: Set of holiday dates
        """
        self.holidays = holidays or set()

    def is_working_day(self, check_date: date) -> bool:
        """Check if date is a working day."""
        # Monday is 0, Sunday is 6
        if check_date.weekday() >= 5:  # Saturday or Sunday
            return False
        return not self.is_holiday(check_date)

    def is_holiday(self, check_date: date) -> bool:
        """Check if date is a holiday."""
        return check_date in self.holidays

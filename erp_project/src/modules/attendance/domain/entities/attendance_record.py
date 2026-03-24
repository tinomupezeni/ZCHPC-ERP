"""
AttendanceRecord aggregate root.
"""

from datetime import date, datetime, time
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.attendance.domain.value_objects import (
    AttendanceStatus,
    ClockTime,
    WorkDuration,
)


class AttendanceRecord(AggregateRoot[int]):
    """
    AttendanceRecord aggregate root.

    Represents a single day's attendance record for an employee.
    Tracks clock-in and clock-out times.
    """

    # Standard work hours for late detection
    STANDARD_START_TIME = time(8, 0)  # 8:00 AM
    STANDARD_END_TIME = time(17, 0)  # 5:00 PM
    LATE_THRESHOLD_MINUTES = 15  # Grace period

    def __init__(
        self,
        id: int,
        employee_id: int,
        record_date: date,
        time_in: ClockTime | None = None,
        time_out: ClockTime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize attendance record."""
        super().__init__(id)
        self.employee_id = employee_id
        self.record_date = record_date
        self.time_in = time_in
        self.time_out = time_out
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate attendance record."""
        if not self.employee_id:
            raise ValidationError(
                message="Employee ID is required",
                code="MISSING_EMPLOYEE_ID",
            )
        if not self.record_date:
            raise ValidationError(
                message="Record date is required",
                code="MISSING_DATE",
            )
        if self.time_out and not self.time_in:
            raise ValidationError(
                message="Cannot have clock-out without clock-in",
                code="INVALID_CLOCK_SEQUENCE",
            )

    @classmethod
    def create_for_clock_in(
        cls,
        id: int,
        employee_id: int,
        record_date: date,
        clock_in_time: ClockTime,
    ) -> "AttendanceRecord":
        """Create a new attendance record with clock-in."""
        return cls(
            id=id,
            employee_id=employee_id,
            record_date=record_date,
            time_in=clock_in_time,
        )

    def clock_in(self, clock_time: ClockTime) -> None:
        """
        Record clock-in time.

        Args:
            clock_time: The clock-in time

        Raises:
            ValidationError: If already clocked in
        """
        if self.time_in is not None:
            raise ValidationError(
                message="Already clocked in for this day",
                code="ALREADY_CLOCKED_IN",
            )
        self.time_in = clock_time
        self.updated_at = datetime.utcnow()

    def clock_out(self, clock_time: ClockTime) -> WorkDuration:
        """
        Record clock-out time.

        Args:
            clock_time: The clock-out time

        Returns:
            The total work duration for the day

        Raises:
            ValidationError: If not clocked in or already clocked out
        """
        if self.time_in is None:
            raise ValidationError(
                message="Cannot clock out without clocking in first",
                code="NOT_CLOCKED_IN",
            )
        if self.time_out is not None:
            raise ValidationError(
                message="Already clocked out for this day",
                code="ALREADY_CLOCKED_OUT",
            )

        self.time_out = clock_time
        self.updated_at = datetime.utcnow()
        return self.work_duration

    @property
    def is_clocked_in(self) -> bool:
        """Check if employee is currently clocked in (no clock-out yet)."""
        return self.time_in is not None and self.time_out is None

    @property
    def is_complete(self) -> bool:
        """Check if attendance record is complete (both in and out)."""
        return self.time_in is not None and self.time_out is not None

    @property
    def work_duration(self) -> WorkDuration:
        """Calculate work duration for the day."""
        if not self.is_complete:
            return WorkDuration.zero()
        return WorkDuration.from_clock_times(self.time_in, self.time_out)

    @property
    def status(self) -> AttendanceStatus:
        """
        Determine attendance status based on clock times.

        Returns:
            AttendanceStatus based on clock-in time and work duration
        """
        if self.time_in is None:
            return AttendanceStatus.ABSENT

        # Check if late (more than threshold after standard start)
        late_threshold = self.time_in.to_minutes() - (
            self.STANDARD_START_TIME.hour * 60 + self.STANDARD_START_TIME.minute
        )

        if late_threshold > self.LATE_THRESHOLD_MINUTES:
            return AttendanceStatus.LATE

        # Check for half day (less than 4 hours worked)
        if self.is_complete and self.work_duration.total_hours < 4:
            return AttendanceStatus.HALF_DAY

        return AttendanceStatus.PRESENT

    @property
    def is_late(self) -> bool:
        """Check if employee arrived late."""
        return self.status == AttendanceStatus.LATE

    def update_times(
        self,
        time_in: ClockTime | None = None,
        time_out: ClockTime | None = None,
    ) -> None:
        """
        Update clock times (admin override).

        Args:
            time_in: New clock-in time
            time_out: New clock-out time
        """
        if time_in is not None:
            self.time_in = time_in
        if time_out is not None:
            if self.time_in is None:
                raise ValidationError(
                    message="Cannot set clock-out without clock-in",
                    code="INVALID_CLOCK_SEQUENCE",
                )
            self.time_out = time_out
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        status = "In Progress" if self.is_clocked_in else self.status.value
        return f"Attendance({self.employee_id}, {self.record_date}, {status})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"AttendanceRecord(id={self.id}, employee_id={self.employee_id}, "
            f"date={self.record_date}, time_in={self.time_in}, time_out={self.time_out})"
        )

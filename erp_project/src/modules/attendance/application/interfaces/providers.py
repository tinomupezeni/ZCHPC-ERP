"""
Attendance provider interfaces.

Interfaces exposed to other modules for accessing attendance data.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Protocol, Sequence


@dataclass(frozen=True)
class AttendanceRecordDTO:
    """Data transfer object for attendance records."""

    id: int
    employee_id: int
    record_date: date
    time_in: time | None
    time_out: time | None
    status: str
    hours_worked: Decimal
    is_late: bool


@dataclass(frozen=True)
class AttendanceSummaryDTO:
    """Data transfer object for attendance summary."""

    employee_id: int
    period_start: date
    period_end: date
    days_present: int
    days_absent: int
    days_late: int
    days_half_day: int
    days_on_leave: int
    total_hours_worked: Decimal
    average_hours_per_day: Decimal
    attendance_rate: Decimal


@dataclass(frozen=True)
class QRTokenDTO:
    """Data transfer object for QR tokens."""

    token: str
    expires_at: datetime
    seconds_remaining: int


class IAttendanceProvider(Protocol):
    """
    Interface for attendance data exposed to other modules.

    Used by payroll module for calculating work days and hours.
    """

    def get_attendance_record(
        self, employee_id: int, record_date: date
    ) -> AttendanceRecordDTO | None:
        """Get attendance record for employee on a specific date."""
        ...

    def get_attendance_in_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[AttendanceRecordDTO]:
        """Get attendance records for employee in a period."""
        ...

    def get_attendance_summary(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> AttendanceSummaryDTO:
        """Get attendance summary for employee in a period."""
        ...

    def get_work_days_count(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """Get number of days worked in period."""
        ...

    def get_total_hours_worked(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Get total hours worked in period."""
        ...

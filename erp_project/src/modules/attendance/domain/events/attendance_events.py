"""
Attendance domain events.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from shared.domain.base import DomainEvent

from modules.attendance.domain.value_objects import ClockTime, WorkDuration


@dataclass(frozen=True)
class EmployeeClockedIn(DomainEvent):
    """Event raised when an employee clocks in."""

    employee_id: int
    record_date: date
    clock_in_time: ClockTime
    is_late: bool

    @property
    def event_type(self) -> str:
        return "attendance.employee_clocked_in"


@dataclass(frozen=True)
class EmployeeClockedOut(DomainEvent):
    """Event raised when an employee clocks out."""

    employee_id: int
    record_date: date
    clock_out_time: ClockTime
    work_duration: WorkDuration

    @property
    def event_type(self) -> str:
        return "attendance.employee_clocked_out"


@dataclass(frozen=True)
class QRTokenGenerated(DomainEvent):
    """Event raised when a new QR token is generated."""

    token_id: int
    expires_at: datetime

    @property
    def event_type(self) -> str:
        return "attendance.qr_token_generated"


@dataclass(frozen=True)
class QRTokenUsed(DomainEvent):
    """Event raised when a QR token is used for clock-in."""

    token_id: int
    employee_id: int
    used_at: datetime

    @property
    def event_type(self) -> str:
        return "attendance.qr_token_used"


@dataclass(frozen=True)
class AttendanceRecordUpdated(DomainEvent):
    """Event raised when an attendance record is manually updated."""

    record_id: int
    employee_id: int
    record_date: date
    updated_by: int  # User ID who made the update
    changes: dict[str, Any]

    @property
    def event_type(self) -> str:
        return "attendance.record_updated"

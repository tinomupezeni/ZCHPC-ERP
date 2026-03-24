"""
Attendance domain layer.

Contains entities, value objects, domain services, and events.
"""

from modules.attendance.domain.entities import AttendanceRecord, QRToken
from modules.attendance.domain.value_objects import (
    AttendanceStatus,
    AttendanceSummary,
    ClockTime,
    TokenExpiry,
    TokenValue,
    WorkDuration,
)

__all__ = [
    "AttendanceRecord",
    "QRToken",
    "AttendanceStatus",
    "AttendanceSummary",
    "ClockTime",
    "WorkDuration",
    "TokenValue",
    "TokenExpiry",
]

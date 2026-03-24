"""
Attendance domain events.
"""

from modules.attendance.domain.events.attendance_events import (
    AttendanceRecordUpdated,
    EmployeeClockedIn,
    EmployeeClockedOut,
    QRTokenGenerated,
    QRTokenUsed,
)

__all__ = [
    "EmployeeClockedIn",
    "EmployeeClockedOut",
    "QRTokenGenerated",
    "QRTokenUsed",
    "AttendanceRecordUpdated",
]

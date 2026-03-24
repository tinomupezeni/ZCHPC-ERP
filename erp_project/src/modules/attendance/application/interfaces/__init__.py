"""
Attendance application interfaces.
"""

from modules.attendance.application.interfaces.providers import (
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
    IAttendanceProvider,
    QRTokenDTO,
)
from modules.attendance.application.interfaces.repositories import (
    IAttendanceRepository,
    IQRTokenRepository,
)

__all__ = [
    "IAttendanceRepository",
    "IQRTokenRepository",
    "IAttendanceProvider",
    "AttendanceRecordDTO",
    "AttendanceSummaryDTO",
    "QRTokenDTO",
]

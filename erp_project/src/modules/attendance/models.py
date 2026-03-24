"""
Attendance module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.attendance.infrastructure.persistence.models import (
    AttendanceRecord,
)

__all__ = [
    "AttendanceRecord",
]

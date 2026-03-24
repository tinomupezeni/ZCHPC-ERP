"""
Attendance repository interfaces.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence

from modules.attendance.domain.entities import AttendanceRecord, QRToken


class IAttendanceRepository(ABC):
    """Interface for attendance record repository."""

    @abstractmethod
    def get_by_id(self, record_id: int) -> AttendanceRecord | None:
        """Get attendance record by ID."""
        ...

    @abstractmethod
    def get_by_employee_and_date(
        self, employee_id: int, record_date: date
    ) -> AttendanceRecord | None:
        """Get attendance record for employee on specific date."""
        ...

    @abstractmethod
    def get_by_employee_in_range(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[AttendanceRecord]:
        """Get attendance records for employee in date range."""
        ...

    @abstractmethod
    def get_by_date(self, record_date: date) -> Sequence[AttendanceRecord]:
        """Get all attendance records for a specific date."""
        ...

    @abstractmethod
    def save(self, record: AttendanceRecord) -> AttendanceRecord:
        """Save attendance record."""
        ...

    @abstractmethod
    def delete(self, record_id: int) -> None:
        """Delete attendance record."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...


class IQRTokenRepository(ABC):
    """Interface for QR token repository."""

    @abstractmethod
    def get_by_id(self, token_id: int) -> QRToken | None:
        """Get QR token by ID."""
        ...

    @abstractmethod
    def get_by_token_value(self, token_value: str) -> QRToken | None:
        """Get QR token by token string."""
        ...

    @abstractmethod
    def get_current_active(self) -> QRToken | None:
        """Get the currently active (non-expired) token."""
        ...

    @abstractmethod
    def save(self, token: QRToken) -> QRToken:
        """Save QR token."""
        ...

    @abstractmethod
    def deactivate_all(self) -> int:
        """
        Deactivate all active tokens.

        Returns:
            Number of tokens deactivated
        """
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...

"""
Portal attendance service.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from shared.domain.exceptions import ValidationError
from modules.portal.application.interfaces import (
    IAttendanceProvider,
    IQRTokenRepository,
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
)
from modules.portal.domain.value_objects import QRToken, ClockStatus


@dataclass
class ClockResult:
    """Result of clock in/out operation."""

    success: bool
    record: Optional[AttendanceRecordDTO] = None
    message: Optional[str] = None


class PortalAttendanceService:
    """
    Attendance service for employee portal.

    Handles clock in/out operations and QR token management.
    """

    def __init__(
        self,
        attendance_provider: IAttendanceProvider,
        qr_token_repo: IQRTokenRepository,
    ) -> None:
        self._attendance_provider = attendance_provider
        self._qr_token_repo = qr_token_repo

    def get_today_status(
        self,
        employee_id: int,
    ) -> ClockStatus:
        """
        Get today's clock status for an employee.

        Returns:
            ClockStatus indicating if clocked in and times
        """
        record = self._attendance_provider.get_today_status(employee_id)

        if record is None:
            return ClockStatus(is_clocked_in=False)

        is_clocked_in = record.time_in is not None and record.time_out is None

        return ClockStatus(
            is_clocked_in=is_clocked_in,
            clock_in_time=record.time_in,
            clock_out_time=record.time_out,
        )

    def clock_in(
        self,
        employee_id: int,
    ) -> ClockResult:
        """
        Clock in an employee.

        Returns:
            ClockResult with attendance record
        """
        # Check if already clocked in
        status = self.get_today_status(employee_id)
        if status.is_clocked_in:
            return ClockResult(
                success=False,
                message="Already clocked in today"
            )

        # Check if already clocked out (prevent double attendance)
        if status.clock_out_time is not None:
            return ClockResult(
                success=False,
                message="Already completed attendance for today"
            )

        try:
            record = self._attendance_provider.clock_in(employee_id)
            return ClockResult(
                success=True,
                record=record,
                message="Clocked in successfully"
            )
        except Exception as e:
            return ClockResult(
                success=False,
                message=str(e)
            )

    def clock_out(
        self,
        employee_id: int,
    ) -> ClockResult:
        """
        Clock out an employee.

        Returns:
            ClockResult with attendance record
        """
        # Check if clocked in
        status = self.get_today_status(employee_id)
        if not status.is_clocked_in:
            return ClockResult(
                success=False,
                message="Not clocked in today"
            )

        try:
            record = self._attendance_provider.clock_out(employee_id)
            return ClockResult(
                success=True,
                record=record,
                message="Clocked out successfully"
            )
        except Exception as e:
            return ClockResult(
                success=False,
                message=str(e)
            )

    def clock_with_qr(
        self,
        employee_id: int,
        token: str,
    ) -> ClockResult:
        """
        Clock in or out using QR token.

        Args:
            employee_id: Employee ID
            token: QR token scanned by employee

        Returns:
            ClockResult indicating success or failure
        """
        # Verify token
        if not self._qr_token_repo.verify_token(token):
            return ClockResult(
                success=False,
                message="Invalid or expired QR code"
            )

        # Increment usage for audit
        self._qr_token_repo.increment_usage(token)

        # Determine if should clock in or out
        status = self.get_today_status(employee_id)

        if status.is_clocked_in:
            return self.clock_out(employee_id)
        elif status.clock_out_time is None:
            return self.clock_in(employee_id)
        else:
            return ClockResult(
                success=False,
                message="Already completed attendance for today"
            )

    def get_current_qr_token(self) -> str:
        """
        Get or generate current QR token.

        Returns:
            Current active QR token string
        """
        token = self._qr_token_repo.get_current_token()

        if token is None:
            # Generate new token
            qr_token = QRToken.generate(validity_seconds=30)
            self._qr_token_repo.create_token(
                token=qr_token.token,
                expires_at=qr_token.expires_at,
            )
            return qr_token.token

        return token

    def get_attendance_history(
        self,
        employee_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[AttendanceRecordDTO]:
        """
        Get attendance history for an employee.

        Args:
            employee_id: Employee ID
            from_date: Start date (defaults to 30 days ago)
            to_date: End date (defaults to today)

        Returns:
            List of attendance records
        """
        if to_date is None:
            to_date = date.today()
        if from_date is None:
            from_date = to_date - timedelta(days=30)

        return self._attendance_provider.get_history(
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date,
        )

    def get_monthly_summary(
        self,
        employee_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> AttendanceSummaryDTO:
        """
        Get monthly attendance summary.

        Args:
            employee_id: Employee ID
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            AttendanceSummaryDTO with statistics
        """
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        return self._attendance_provider.get_monthly_summary(
            employee_id=employee_id,
            year=year,
            month=month,
        )

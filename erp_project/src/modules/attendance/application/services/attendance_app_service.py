"""
Attendance application service.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Sequence

from shared.infrastructure.event_bus import EventBus

from modules.attendance.application.interfaces import (
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
    IAttendanceRepository,
)
from modules.attendance.domain.entities import AttendanceRecord
from modules.attendance.domain.events import EmployeeClockedIn, EmployeeClockedOut
from modules.attendance.domain.services import (
    AttendanceSummaryCalculator,
    LateArrivalDetector,
)
from modules.attendance.domain.value_objects import ClockTime


@dataclass
class ClockInCommand:
    """Command for clocking in."""

    employee_id: int
    clock_time: datetime | None = None


@dataclass
class ClockOutCommand:
    """Command for clocking out."""

    employee_id: int
    clock_time: datetime | None = None


@dataclass
class UpdateAttendanceCommand:
    """Command for updating attendance (admin)."""

    record_id: int
    time_in: str | None = None  # HH:MM format
    time_out: str | None = None  # HH:MM format
    updated_by: int | None = None


class AttendanceService:
    """
    Application service for attendance operations.

    Orchestrates attendance-related use cases.
    """

    def __init__(
        self,
        attendance_repo: IAttendanceRepository,
        event_bus: EventBus | None = None,
        late_detector: LateArrivalDetector | None = None,
        summary_calculator: AttendanceSummaryCalculator | None = None,
    ):
        """
        Initialize service.

        Args:
            attendance_repo: Attendance repository
            event_bus: Event bus for publishing domain events
            late_detector: Late arrival detector
            summary_calculator: Summary calculator
        """
        self.attendance_repo = attendance_repo
        self.event_bus = event_bus
        self.late_detector = late_detector or LateArrivalDetector()
        self.summary_calculator = summary_calculator or AttendanceSummaryCalculator(
            self.late_detector
        )

    def clock_in(self, command: ClockInCommand) -> AttendanceRecord:
        """
        Clock in an employee.

        Args:
            command: Clock-in command

        Returns:
            The created/updated attendance record

        Raises:
            ValidationError: If already clocked in
        """
        now = command.clock_time or datetime.now()
        today = now.date()
        clock_time = ClockTime.from_time(now.time())

        # Check for existing record
        existing = self.attendance_repo.get_by_employee_and_date(
            command.employee_id, today
        )

        if existing:
            # Record exists - clock in on existing record
            existing.clock_in(clock_time)
            record = self.attendance_repo.save(existing)
        else:
            # Create new record
            record = AttendanceRecord.create_for_clock_in(
                id=self.attendance_repo.get_next_id(),
                employee_id=command.employee_id,
                record_date=today,
                clock_in_time=clock_time,
            )
            record = self.attendance_repo.save(record)

        # Publish event
        if self.event_bus:
            event = EmployeeClockedIn(
                employee_id=command.employee_id,
                record_date=today,
                clock_in_time=clock_time,
                is_late=self.late_detector.is_late(clock_time),
            )
            self.event_bus.publish(event)

        return record

    def clock_out(self, command: ClockOutCommand) -> AttendanceRecord:
        """
        Clock out an employee.

        Args:
            command: Clock-out command

        Returns:
            The updated attendance record

        Raises:
            ValidationError: If not clocked in or already clocked out
        """
        now = command.clock_time or datetime.now()
        today = now.date()
        clock_time = ClockTime.from_time(now.time())

        # Get existing record
        record = self.attendance_repo.get_by_employee_and_date(
            command.employee_id, today
        )

        if not record:
            from shared.domain.exceptions import ValidationError

            raise ValidationError(
                message="No attendance record found for today. Please clock in first.",
                code="NO_RECORD_FOUND",
            )

        work_duration = record.clock_out(clock_time)
        record = self.attendance_repo.save(record)

        # Publish event
        if self.event_bus:
            event = EmployeeClockedOut(
                employee_id=command.employee_id,
                record_date=today,
                clock_out_time=clock_time,
                work_duration=work_duration,
            )
            self.event_bus.publish(event)

        return record

    def get_today_status(self, employee_id: int) -> AttendanceRecordDTO | None:
        """
        Get today's attendance status for an employee.

        Args:
            employee_id: The employee ID

        Returns:
            Today's attendance record DTO or None
        """
        today = date.today()
        record = self.attendance_repo.get_by_employee_and_date(employee_id, today)

        if not record:
            return None

        return self._to_dto(record)

    def get_history(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[AttendanceRecordDTO]:
        """
        Get attendance history for an employee.

        Args:
            employee_id: The employee ID
            start_date: Start of period
            end_date: End of period

        Returns:
            List of attendance record DTOs
        """
        records = self.attendance_repo.get_by_employee_in_range(
            employee_id, start_date, end_date
        )
        return [self._to_dto(r) for r in records]

    def get_filtered_history(
        self,
        department_id: int | None = None,
        employee_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[AttendanceRecordDTO]:
        """
        Get attendance records across employees, filtered by department/employee/date range.

        Used by admin/HR views to list attendance beyond the requesting user's own record.
        """
        records = self.attendance_repo.get_filtered(
            department_id=department_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [self._to_dto(r) for r in records]

    def get_summary(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> AttendanceSummaryDTO:
        """
        Get attendance summary for an employee.

        Args:
            employee_id: The employee ID
            start_date: Start of period
            end_date: End of period

        Returns:
            Attendance summary DTO
        """
        records = self.attendance_repo.get_by_employee_in_range(
            employee_id, start_date, end_date
        )
        summary = self.summary_calculator.calculate(list(records))

        return AttendanceSummaryDTO(
            employee_id=employee_id,
            period_start=start_date,
            period_end=end_date,
            days_present=summary.days_present,
            days_absent=summary.days_absent,
            days_late=summary.days_late,
            days_half_day=summary.days_half_day,
            days_on_leave=summary.days_on_leave,
            total_hours_worked=summary.total_hours_worked,
            average_hours_per_day=summary.average_hours_per_day,
            attendance_rate=summary.attendance_rate,
        )

    def update_attendance(self, command: UpdateAttendanceCommand) -> AttendanceRecord:
        """
        Update attendance record (admin function).

        Args:
            command: Update command

        Returns:
            Updated attendance record
        """
        record = self.attendance_repo.get_by_id(command.record_id)

        if not record:
            from shared.domain.exceptions import ValidationError

            raise ValidationError(
                message="Attendance record not found",
                code="RECORD_NOT_FOUND",
            )

        time_in = ClockTime.from_string(command.time_in) if command.time_in else None
        time_out = ClockTime.from_string(command.time_out) if command.time_out else None

        record.update_times(time_in=time_in, time_out=time_out)
        return self.attendance_repo.save(record)

    def _to_dto(self, record: AttendanceRecord) -> AttendanceRecordDTO:
        """Convert entity to DTO."""
        return AttendanceRecordDTO(
            id=record.id,
            employee_id=record.employee_id,
            record_date=record.record_date,
            time_in=record.time_in.to_time() if record.time_in else None,
            time_out=record.time_out.to_time() if record.time_out else None,
            status=record.status.value,
            hours_worked=record.work_duration.total_hours,
            is_late=record.is_late,
        )

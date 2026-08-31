"""
Django ORM implementation of attendance repository.
"""

from datetime import date, datetime
from typing import Sequence, Type

from modules.attendance.application.interfaces import IAttendanceRepository
from modules.attendance.domain.entities import AttendanceRecord
from modules.attendance.domain.value_objects import ClockTime


class DjangoAttendanceRepository(IAttendanceRepository):
    """
    Django ORM implementation of attendance repository.

    Maps AttendanceRecord domain entity to Django ORM model.
    """

    def __init__(self) -> None:
        """Initialize repository."""
        self._model: Type | None = None

    @property
    def model(self):
        """Lazy load the Django model to avoid circular imports."""
        if self._model is None:
            from modules.attendance.infrastructure.persistence.models import AttendanceRecord as AttendanceModel

            self._model = AttendanceModel
        return self._model

    def get_by_id(self, record_id: int) -> AttendanceRecord | None:
        """Get attendance record by ID."""
        try:
            db_record = self.model.objects.get(pk=record_id)
            return self._to_entity(db_record)
        except self.model.DoesNotExist:
            return None

    def get_by_employee_and_date(
        self, employee_id: int, record_date: date
    ) -> AttendanceRecord | None:
        """Get attendance record for employee on specific date."""
        try:
            db_record = self.model.objects.get(
                employee_id=employee_id,
                date=record_date,
            )
            return self._to_entity(db_record)
        except self.model.DoesNotExist:
            return None

    def get_by_employee_in_range(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[AttendanceRecord]:
        """Get attendance records for employee in date range."""
        db_records = self.model.objects.filter(
            employee_id=employee_id,
            date__gte=start_date,
            date__lte=end_date,
        ).order_by("-date")
        return [self._to_entity(r) for r in db_records]

    def get_by_date(self, record_date: date) -> Sequence[AttendanceRecord]:
        """Get all attendance records for a specific date."""
        db_records = self.model.objects.filter(date=record_date).order_by(
            "employee__first_name"
        )
        return [self._to_entity(r) for r in db_records]

    def get_filtered(
        self,
        department_id: int | None = None,
        employee_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[AttendanceRecord]:
        """Get attendance records filtered by department/employee/date range."""
        queryset = self.model.objects.all()

        if department_id is not None:
            queryset = queryset.filter(employee__department_id=department_id)
        if employee_id is not None:
            queryset = queryset.filter(employee_id=employee_id)
        if start_date is not None:
            queryset = queryset.filter(date__gte=start_date)
        if end_date is not None:
            queryset = queryset.filter(date__lte=end_date)

        queryset = queryset.order_by("-date", "employee__first_name")
        return [self._to_entity(r) for r in queryset]

    def save(self, record: AttendanceRecord) -> AttendanceRecord:
        """Save attendance record."""
        time_in = record.time_in.to_time() if record.time_in else None
        time_out = record.time_out.to_time() if record.time_out else None

        if record.id:
            # Update existing
            updated = self.model.objects.filter(pk=record.id).update(
                employee_id=record.employee_id,
                date=record.record_date,
                time_in=time_in,
                time_out=time_out,
            )
            if updated == 0:
                # Record doesn't exist, create it
                db_record = self.model.objects.create(
                    employee_id=record.employee_id,
                    date=record.record_date,
                    time_in=time_in,
                    time_out=time_out,
                )
                record = self._to_entity(db_record)
        else:
            # Create new
            db_record = self.model.objects.create(
                employee_id=record.employee_id,
                date=record.record_date,
                time_in=time_in,
                time_out=time_out,
            )
            record = self._to_entity(db_record)

        return record

    def delete(self, record_id: int) -> None:
        """Delete attendance record."""
        self.model.objects.filter(pk=record_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = self.model.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, db_record) -> AttendanceRecord:
        """Convert Django model to domain entity."""
        time_in = None
        time_out = None

        if db_record.time_in:
            time_in = ClockTime.from_time(db_record.time_in)
        if db_record.time_out:
            time_out = ClockTime.from_time(db_record.time_out)

        return AttendanceRecord(
            id=db_record.id,
            employee_id=db_record.employee_id,
            record_date=db_record.date,
            time_in=time_in,
            time_out=time_out,
        )

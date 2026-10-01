"""
Django ORM implementation of ILeaveRequestRepository.
"""

from datetime import date
from typing import Sequence

from django.db.models import Q

from modules.leave.infrastructure.persistence.models import LeaveRequest as LeaveRequestModel

from modules.leave.application.interfaces import ILeaveRequestRepository
from modules.leave.domain.entities import LeaveRequest
from modules.leave.domain.value_objects import LeavePeriod, LeaveStatus


class DjangoLeaveRequestRepository(ILeaveRequestRepository):
    """Django ORM implementation of leave request repository."""

    def get_by_id(self, request_id: int) -> LeaveRequest | None:
        """Get request by ID."""
        try:
            model = LeaveRequestModel.objects.select_related(
                "employee", "leave_type", "reviewed_by"
            ).get(id=request_id)
            return self._to_entity(model)
        except LeaveRequestModel.DoesNotExist:
            return None

    def get_by_employee(
        self,
        employee_id: int,
        year: int | None = None,
        status: LeaveStatus | None = None,
    ) -> Sequence[LeaveRequest]:
        """Get requests for employee with optional filters."""
        queryset = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        ).filter(employee_id=employee_id)

        if year is not None:
            queryset = queryset.filter(start_date__year=year)

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return [self._to_entity(model) for model in queryset]

    def get_by_employee_and_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequest]:
        """Get requests for employee in a date range."""
        queryset = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        ).filter(
            employee_id=employee_id,
            # Overlapping dates
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        return [self._to_entity(model) for model in queryset]

    def get_pending_requests(
        self,
        employee_id: int | None = None,
    ) -> Sequence[LeaveRequest]:
        """Get pending requests, optionally filtered by employee."""
        queryset = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        ).filter(status=LeaveStatus.PENDING.value)

        if employee_id is not None:
            queryset = queryset.filter(employee_id=employee_id)

        return [self._to_entity(model) for model in queryset]

    def get_approved_requests_in_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequest]:
        """Get approved requests in a period."""
        queryset = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        ).filter(
            employee_id=employee_id,
            status=LeaveStatus.APPROVED.value,
            # Overlapping dates
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        return [self._to_entity(model) for model in queryset]

    def save(self, request: LeaveRequest) -> LeaveRequest:
        """Save request."""
        model, created = LeaveRequestModel.objects.update_or_create(
            id=request.id,
            defaults={
                "employee_id": request.employee_id,
                "leave_type_id": request.leave_type_id,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "reason": request.reason,
                "status": request.status.value,
                "reviewed_by_id": request.reviewed_by_id,
                "review_date": request.reviewed_at,
            },
        )
        # Reload with relationships
        model = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        ).get(id=model.id)
        return self._to_entity(model)

    def delete(self, request_id: int) -> None:
        """Delete request."""
        LeaveRequestModel.objects.filter(id=request_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = LeaveRequestModel.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, model: LeaveRequestModel) -> LeaveRequest:
        """Convert Django model to domain entity."""
        period = LeavePeriod(
            start_date=model.start_date,
            end_date=model.end_date,
        )

        # Map status string to enum
        status_map = {
            "Pending": LeaveStatus.PENDING,
            "Approved": LeaveStatus.APPROVED,
            "Rejected": LeaveStatus.REJECTED,
            "Cancelled": LeaveStatus.CANCELLED,
        }
        status = status_map.get(model.status, LeaveStatus.PENDING)

        return LeaveRequest(
            id=model.id,
            employee_id=model.employee_id,
            leave_type_id=model.leave_type_id,
            period=period,
            reason=model.reason or "",
            status=status,
            requested_at=model.requested_on,
            reviewed_by_id=model.reviewed_by_id,
            reviewed_at=model.review_date,
        )

"""
Leave request application service.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.leave.application.interfaces import (
    ILeaveBalanceRepository,
    ILeaveRequestRepository,
    ILeaveTypeRepository,
    LeaveRequestDTO,
    LeaveRequestSummaryDTO,
)
from modules.leave.domain.entities import LeaveRequest
from modules.leave.domain.events import LeaveApproved, LeaveCancelled, LeaveRejected, LeaveRequested
from modules.leave.domain.services import (
    ILeaveApprovalPolicy,
    ILeaveBalanceCalculator,
    ILeaveConflictDetector,
)
from modules.leave.domain.value_objects import LeaveEntitlement, LeavePeriod, LeaveStatus


@dataclass
class SubmitLeaveRequestCommand:
    """Command to submit a leave request."""

    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str = ""


@dataclass
class ReviewLeaveRequestCommand:
    """Command to approve or reject a leave request."""

    request_id: int
    reviewer_id: int
    approved: bool
    rejection_reason: str | None = None


@dataclass
class CancelLeaveRequestCommand:
    """Command to cancel a leave request."""

    request_id: int


class LeaveRequestService:
    """
    Application service for leave request operations.

    Handles use cases related to leave requests.
    """

    def __init__(
        self,
        request_repository: ILeaveRequestRepository,
        balance_repository: ILeaveBalanceRepository,
        leave_type_repository: ILeaveTypeRepository,
        conflict_detector: ILeaveConflictDetector,
        balance_calculator: ILeaveBalanceCalculator,
        approval_policy: ILeaveApprovalPolicy,
    ) -> None:
        self._request_repository = request_repository
        self._balance_repository = balance_repository
        self._leave_type_repository = leave_type_repository
        self._conflict_detector = conflict_detector
        self._balance_calculator = balance_calculator
        self._approval_policy = approval_policy

    def submit_leave_request(
        self, command: SubmitLeaveRequestCommand
    ) -> LeaveRequestDTO:
        """Submit a new leave request."""
        # Verify leave type exists and is active
        leave_type = self._leave_type_repository.get_by_id(command.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {command.leave_type_id} not found")
        if not leave_type.is_active:
            raise ValidationError(f"Leave type '{leave_type.name}' is not active")

        # Create leave period
        period = LeavePeriod(
            start_date=command.start_date,
            end_date=command.end_date,
        )

        # Get year from start date
        year = command.start_date.year

        # Check for sufficient balance
        balance = self._balance_repository.get_by_employee_and_type_and_year(
            employee_id=command.employee_id,
            leave_type_id=command.leave_type_id,
            year=year,
        )
        if not balance:
            raise ValidationError(
                f"No leave balance found for employee {command.employee_id} "
                f"for leave type '{leave_type.name}' in year {year}"
            )

        # Get pending requests for available days calculation
        pending_requests = self._request_repository.get_by_employee(
            employee_id=command.employee_id,
            year=year,
            status=LeaveStatus.PENDING,
        )
        available_days = self._balance_calculator.calculate_available_days(
            balance=balance,
            pending_requests=pending_requests,
        )

        if period.days > available_days:
            raise ValidationError(
                f"Insufficient leave balance. Requested {period.days} days, "
                f"but only {available_days} days available"
            )

        # Check for conflicts
        existing_requests = self._request_repository.get_by_employee(
            employee_id=command.employee_id,
            year=year,
        )

        # Create the request
        request = LeaveRequest(
            id=self._request_repository.get_next_id(),
            employee_id=command.employee_id,
            leave_type_id=command.leave_type_id,
            period=period,
            reason=command.reason,
        )

        conflicts = self._conflict_detector.find_conflicts(
            request=request,
            existing_requests=existing_requests,
        )
        if conflicts:
            conflict_dates = ", ".join(
                f"{c.start_date} to {c.end_date}" for c in conflicts
            )
            raise ValidationError(f"Leave request conflicts with existing requests: {conflict_dates}")

        # Add domain event
        request.add_domain_event(
            LeaveRequested(
                request_id=request.id,
                employee_id=request.employee_id,
                leave_type_id=request.leave_type_id,
                start_date=request.start_date,
                end_date=request.end_date,
                days=request.days,
                requested_at=datetime.now(),
            )
        )

        saved = self._request_repository.save(request)
        return self._to_dto(saved, leave_type.name)

    def approve_leave_request(
        self, command: ReviewLeaveRequestCommand
    ) -> LeaveRequestDTO:
        """Approve a leave request."""
        if not command.approved:
            raise ValidationError("Use reject method for rejecting requests")

        request = self._request_repository.get_by_id(command.request_id)
        if not request:
            raise NotFoundError(f"Leave request with ID {command.request_id} not found")

        leave_type = self._leave_type_repository.get_by_id(request.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {request.leave_type_id} not found")

        # Check approval policy
        can_approve, reason = self._approval_policy.can_approve(
            request=request,
            reviewer_id=command.reviewer_id,
        )
        if not can_approve:
            raise ValidationError(f"Cannot approve request: {reason}")

        # Approve the request
        request.approve(command.reviewer_id)

        # Deduct from balance
        year = request.start_date.year
        balance = self._balance_repository.get_by_employee_and_type_and_year(
            employee_id=request.employee_id,
            leave_type_id=request.leave_type_id,
            year=year,
        )
        if balance:
            balance.deduct(request.days)
            self._balance_repository.save(balance)

        # Add domain event
        request.add_domain_event(
            LeaveApproved(
                request_id=request.id,
                employee_id=request.employee_id,
                leave_type_id=request.leave_type_id,
                days=request.days,
                approved_by_id=command.reviewer_id,
                approved_at=datetime.now(),
            )
        )

        saved = self._request_repository.save(request)
        return self._to_dto(saved, leave_type.name)

    def reject_leave_request(
        self, command: ReviewLeaveRequestCommand
    ) -> LeaveRequestDTO:
        """Reject a leave request."""
        request = self._request_repository.get_by_id(command.request_id)
        if not request:
            raise NotFoundError(f"Leave request with ID {command.request_id} not found")

        leave_type = self._leave_type_repository.get_by_id(request.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {request.leave_type_id} not found")

        # Check approval policy
        can_reject, reason = self._approval_policy.can_reject(
            request=request,
            reviewer_id=command.reviewer_id,
        )
        if not can_reject:
            raise ValidationError(f"Cannot reject request: {reason}")

        # Reject the request
        request.reject(command.reviewer_id)

        # Add domain event
        request.add_domain_event(
            LeaveRejected(
                request_id=request.id,
                employee_id=request.employee_id,
                leave_type_id=request.leave_type_id,
                rejected_by_id=command.reviewer_id,
                rejected_at=datetime.now(),
                rejection_reason=command.rejection_reason or "",
            )
        )

        saved = self._request_repository.save(request)
        return self._to_dto(saved, leave_type.name)

    def cancel_leave_request(
        self, command: CancelLeaveRequestCommand
    ) -> LeaveRequestDTO:
        """Cancel a leave request."""
        request = self._request_repository.get_by_id(command.request_id)
        if not request:
            raise NotFoundError(f"Leave request with ID {command.request_id} not found")

        leave_type = self._leave_type_repository.get_by_id(request.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {request.leave_type_id} not found")

        was_approved = request.status == LeaveStatus.APPROVED

        # Cancel the request
        request.cancel()

        # Restore balance if was approved
        if was_approved:
            year = request.start_date.year
            balance = self._balance_repository.get_by_employee_and_type_and_year(
                employee_id=request.employee_id,
                leave_type_id=request.leave_type_id,
                year=year,
            )
            if balance:
                balance.restore(request.days)
                self._balance_repository.save(balance)

        # Add domain event
        request.add_domain_event(
            LeaveCancelled(
                request_id=request.id,
                employee_id=request.employee_id,
                leave_type_id=request.leave_type_id,
                days=request.days,
                was_approved=was_approved,
                cancelled_at=datetime.now(),
            )
        )

        saved = self._request_repository.save(request)
        return self._to_dto(saved, leave_type.name)

    def get_leave_request(self, request_id: int) -> LeaveRequestDTO:
        """Get a leave request by ID."""
        request = self._request_repository.get_by_id(request_id)
        if not request:
            raise NotFoundError(f"Leave request with ID {request_id} not found")

        leave_type = self._leave_type_repository.get_by_id(request.leave_type_id)
        leave_type_name = leave_type.name if leave_type else "Unknown"
        return self._to_dto(request, leave_type_name)

    def get_employee_requests(
        self,
        employee_id: int,
        year: int | None = None,
        status: LeaveStatus | None = None,
    ) -> Sequence[LeaveRequestDTO]:
        """Get leave requests for an employee."""
        requests = self._request_repository.get_by_employee(
            employee_id=employee_id,
            year=year,
            status=status,
        )

        # Get leave type names
        leave_types = {lt.id: lt.name for lt in self._leave_type_repository.get_all()}

        return [
            self._to_dto(r, leave_types.get(r.leave_type_id, "Unknown"))
            for r in requests
        ]

    def get_pending_requests(
        self,
        employee_id: int | None = None,
    ) -> Sequence[LeaveRequestDTO]:
        """Get pending leave requests."""
        requests = self._request_repository.get_pending_requests(employee_id=employee_id)

        # Get leave type names
        leave_types = {lt.id: lt.name for lt in self._leave_type_repository.get_all()}

        return [
            self._to_dto(r, leave_types.get(r.leave_type_id, "Unknown"))
            for r in requests
        ]

    def get_request_summary(
        self,
        employee_id: int,
        year: int,
    ) -> LeaveRequestSummaryDTO:
        """Get summary of leave requests for an employee."""
        requests = self._request_repository.get_by_employee(
            employee_id=employee_id,
            year=year,
        )

        pending = sum(1 for r in requests if r.status == LeaveStatus.PENDING)
        approved = sum(1 for r in requests if r.status == LeaveStatus.APPROVED)
        rejected = sum(1 for r in requests if r.status == LeaveStatus.REJECTED)
        cancelled = sum(1 for r in requests if r.status == LeaveStatus.CANCELLED)
        total_days_taken = sum(r.days for r in requests if r.status == LeaveStatus.APPROVED)

        return LeaveRequestSummaryDTO(
            employee_id=employee_id,
            year=year,
            total_requests=len(requests),
            pending_requests=pending,
            approved_requests=approved,
            rejected_requests=rejected,
            cancelled_requests=cancelled,
            total_days_taken=total_days_taken,
        )

    def _to_dto(self, request: LeaveRequest, leave_type_name: str) -> LeaveRequestDTO:
        """Convert entity to DTO."""
        return LeaveRequestDTO(
            id=request.id,
            employee_id=request.employee_id,
            leave_type_id=request.leave_type_id,
            leave_type_name=leave_type_name,
            start_date=request.start_date,
            end_date=request.end_date,
            days=request.days,
            reason=request.reason,
            status=request.status.value,
            can_cancel=request.can_cancel,
            requested_at=request.requested_at.isoformat() if request.requested_at else "",
            reviewed_by_id=request.reviewed_by_id,
            reviewed_at=request.reviewed_at.isoformat() if request.reviewed_at else None,
        )

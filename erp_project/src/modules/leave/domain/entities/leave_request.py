"""
LeaveRequest aggregate root.
"""

from datetime import date, datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.leave.domain.value_objects import LeavePeriod, LeaveStatus


class LeaveRequest(AggregateRoot[int]):
    """
    LeaveRequest aggregate root.

    Represents a leave request from an employee.
    """

    def __init__(
        self,
        id: int,
        employee_id: int,
        leave_type_id: int,
        period: LeavePeriod,
        reason: str = "",
        status: LeaveStatus = LeaveStatus.PENDING,
        requested_at: datetime | None = None,
        reviewed_by_id: int | None = None,
        reviewed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize leave request."""
        super().__init__(id)
        self.employee_id = employee_id
        self.leave_type_id = leave_type_id
        self.period = period
        self.reason = reason
        self.status = status
        self.requested_at = requested_at or datetime.utcnow()
        self.reviewed_by_id = reviewed_by_id
        self.reviewed_at = reviewed_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate leave request data."""
        if not self.employee_id:
            raise ValidationError(
                message="Employee ID is required",
                code="MISSING_EMPLOYEE_ID",
            )
        if not self.leave_type_id:
            raise ValidationError(
                message="Leave type ID is required",
                code="MISSING_LEAVE_TYPE_ID",
            )

    @classmethod
    def create(
        cls,
        id: int,
        employee_id: int,
        leave_type_id: int,
        start_date: date,
        end_date: date,
        reason: str = "",
    ) -> "LeaveRequest":
        """
        Create a new leave request.

        Args:
            id: Request ID
            employee_id: Employee ID
            leave_type_id: Leave type ID
            start_date: Start date
            end_date: End date
            reason: Reason for leave

        Returns:
            New LeaveRequest instance
        """
        return cls(
            id=id,
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            period=LeavePeriod(start_date=start_date, end_date=end_date),
            reason=reason.strip() if reason else "",
            status=LeaveStatus.PENDING,
        )

    @property
    def start_date(self) -> date:
        """Get start date."""
        return self.period.start_date

    @property
    def end_date(self) -> date:
        """Get end date."""
        return self.period.end_date

    @property
    def days(self) -> int:
        """Get number of days."""
        return self.period.days

    @property
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == LeaveStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == LeaveStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == LeaveStatus.REJECTED

    @property
    def is_cancelled(self) -> bool:
        """Check if request is cancelled."""
        return self.status == LeaveStatus.CANCELLED

    @property
    def can_cancel(self) -> bool:
        """Check if request can be cancelled."""
        return self.status.can_cancel

    @property
    def can_review(self) -> bool:
        """Check if request can be reviewed (approved/rejected)."""
        return self.status == LeaveStatus.PENDING

    def approve(self, reviewer_id: int) -> None:
        """
        Approve the leave request.

        Args:
            reviewer_id: ID of the reviewer

        Raises:
            ValidationError: If request cannot be approved
        """
        if not self.can_review:
            raise ValidationError(
                message=f"Cannot approve a {self.status.value} request",
                code="CANNOT_APPROVE",
            )

        self.status = LeaveStatus.APPROVED
        self.reviewed_by_id = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self, reviewer_id: int) -> None:
        """
        Reject the leave request.

        Args:
            reviewer_id: ID of the reviewer

        Raises:
            ValidationError: If request cannot be rejected
        """
        if not self.can_review:
            raise ValidationError(
                message=f"Cannot reject a {self.status.value} request",
                code="CANNOT_REJECT",
            )

        self.status = LeaveStatus.REJECTED
        self.reviewed_by_id = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """
        Cancel the leave request.

        Raises:
            ValidationError: If request cannot be cancelled
        """
        if not self.can_cancel:
            raise ValidationError(
                message=f"Cannot cancel a {self.status.value} request",
                code="CANNOT_CANCEL",
            )

        self.status = LeaveStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def overlaps_with(self, other: "LeaveRequest") -> bool:
        """
        Check if this request overlaps with another.

        Args:
            other: Another leave request

        Returns:
            True if periods overlap
        """
        return self.period.overlaps_with(other.period)

    def __str__(self) -> str:
        """String representation."""
        return f"LeaveRequest({self.employee_id}, {self.period}, {self.status.value})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"LeaveRequest(id={self.id}, employee_id={self.employee_id}, "
            f"period={self.period}, status={self.status.value})"
        )

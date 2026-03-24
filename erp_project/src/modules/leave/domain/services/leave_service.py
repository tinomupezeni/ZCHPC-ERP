"""
Leave domain services.
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Sequence

from modules.leave.domain.entities import LeaveBalance, LeaveRequest
from modules.leave.domain.value_objects import LeaveStatus


class ILeaveConflictDetector(ABC):
    """Interface for detecting leave conflicts."""

    @abstractmethod
    def has_conflict(
        self,
        request: LeaveRequest,
        existing_requests: Sequence[LeaveRequest],
    ) -> bool:
        """
        Check if a request conflicts with existing requests.

        Args:
            request: The new leave request
            existing_requests: Existing active requests

        Returns:
            True if there's a conflict
        """
        ...

    @abstractmethod
    def find_conflicts(
        self,
        request: LeaveRequest,
        existing_requests: Sequence[LeaveRequest],
    ) -> list[LeaveRequest]:
        """
        Find all conflicting requests.

        Args:
            request: The new leave request
            existing_requests: Existing active requests

        Returns:
            List of conflicting requests
        """
        ...


class LeaveConflictDetector(ILeaveConflictDetector):
    """
    Default leave conflict detector.

    Detects overlapping leave requests for the same employee.
    """

    def has_conflict(
        self,
        request: LeaveRequest,
        existing_requests: Sequence[LeaveRequest],
    ) -> bool:
        """Check if request conflicts with existing requests."""
        return len(self.find_conflicts(request, existing_requests)) > 0

    def find_conflicts(
        self,
        request: LeaveRequest,
        existing_requests: Sequence[LeaveRequest],
    ) -> list[LeaveRequest]:
        """Find all conflicting requests."""
        conflicts = []
        for existing in existing_requests:
            # Only check active (pending or approved) requests
            if existing.status not in (LeaveStatus.PENDING, LeaveStatus.APPROVED):
                continue

            # Skip same request (for updates)
            if existing.id == request.id:
                continue

            # Check for same employee
            if existing.employee_id != request.employee_id:
                continue

            # Check for overlap
            if request.overlaps_with(existing):
                conflicts.append(existing)

        return conflicts


class ILeaveBalanceCalculator(ABC):
    """Interface for leave balance calculations."""

    @abstractmethod
    def calculate_available_days(
        self,
        balance: LeaveBalance,
        pending_requests: Sequence[LeaveRequest],
    ) -> Decimal:
        """
        Calculate available days considering pending requests.

        Args:
            balance: The current balance
            pending_requests: Pending leave requests

        Returns:
            Available days
        """
        ...


class LeaveBalanceCalculator(ILeaveBalanceCalculator):
    """
    Default leave balance calculator.

    Calculates available leave considering pending requests.
    """

    def calculate_available_days(
        self,
        balance: LeaveBalance,
        pending_requests: Sequence[LeaveRequest],
    ) -> Decimal:
        """Calculate available days considering pending requests."""
        # Start with remaining days
        available = balance.remaining_days

        # Subtract pending request days
        for request in pending_requests:
            if request.status == LeaveStatus.PENDING:
                if request.leave_type_id == balance.leave_type_id:
                    available -= Decimal(str(request.days))

        return max(available, Decimal("0"))


class ILeaveApprovalPolicy(ABC):
    """Interface for leave approval policies."""

    @abstractmethod
    def can_approve(
        self,
        request: LeaveRequest,
        approver_id: int,
    ) -> tuple[bool, str]:
        """
        Check if request can be approved.

        Args:
            request: The leave request
            approver_id: ID of the approver

        Returns:
            Tuple of (can_approve, reason)
        """
        ...

    @abstractmethod
    def can_auto_approve(self, request: LeaveRequest) -> bool:
        """
        Check if request can be auto-approved.

        Args:
            request: The leave request

        Returns:
            True if can be auto-approved
        """
        ...


class DefaultLeaveApprovalPolicy(ILeaveApprovalPolicy):
    """
    Default leave approval policy.

    Basic policy that allows managers to approve leave.
    """

    def __init__(self, auto_approve_days: int = 0):
        """
        Initialize policy.

        Args:
            auto_approve_days: Requests up to this many days are auto-approved
        """
        self.auto_approve_days = auto_approve_days

    def can_approve(
        self,
        request: LeaveRequest,
        approver_id: int,
    ) -> tuple[bool, str]:
        """Check if request can be approved."""
        # Cannot self-approve
        if request.employee_id == approver_id:
            return False, "Cannot approve own leave request"

        # Must be pending
        if not request.is_pending:
            return False, f"Request is already {request.status.value}"

        return True, ""

    def can_auto_approve(self, request: LeaveRequest) -> bool:
        """Check if request can be auto-approved."""
        if self.auto_approve_days <= 0:
            return False
        return request.days <= self.auto_approve_days


class ILeaveYearService(ABC):
    """Interface for leave year-related operations."""

    @abstractmethod
    def get_current_year(self) -> int:
        """Get the current leave year."""
        ...

    @abstractmethod
    def initialize_balances(
        self,
        employee_id: int,
        year: int,
    ) -> list[LeaveBalance]:
        """
        Initialize leave balances for an employee for a year.

        Args:
            employee_id: Employee ID
            year: Year to initialize

        Returns:
            List of created balances
        """
        ...


class DefaultLeaveYearService(ILeaveYearService):
    """Default leave year service."""

    def get_current_year(self) -> int:
        """Get the current leave year."""
        return date.today().year

    def initialize_balances(
        self,
        employee_id: int,
        year: int,
    ) -> list[LeaveBalance]:
        """Initialize leave balances - to be implemented with repository."""
        # This would typically be implemented with repository access
        # For now, return empty list as placeholder
        return []

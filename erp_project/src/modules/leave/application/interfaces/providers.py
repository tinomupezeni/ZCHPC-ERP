"""
Leave provider interfaces.

Interfaces exposed to other modules for accessing leave data.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, Sequence


@dataclass(frozen=True)
class LeaveTypeDTO:
    """Data transfer object for leave types."""

    id: int
    name: str
    default_days_allowed: int
    is_active: bool


@dataclass(frozen=True)
class LeaveBalanceDTO:
    """Data transfer object for leave balances."""

    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: str
    year: int
    entitled_days: Decimal
    used_days: Decimal
    remaining_days: Decimal
    usage_percentage: Decimal


@dataclass(frozen=True)
class LeaveRequestDTO:
    """Data transfer object for leave requests."""

    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: str
    start_date: date
    end_date: date
    days: int
    reason: str
    status: str
    can_cancel: bool
    requested_at: str
    reviewed_by_id: int | None
    reviewed_at: str | None


@dataclass(frozen=True)
class LeaveBalanceSummaryDTO:
    """Summary of leave balances for an employee."""

    employee_id: int
    year: int
    total_entitled: Decimal
    total_used: Decimal
    total_remaining: Decimal
    balances: Sequence[LeaveBalanceDTO]


@dataclass(frozen=True)
class LeaveRequestSummaryDTO:
    """Summary of leave requests for an employee."""

    employee_id: int
    year: int
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    cancelled_requests: int
    total_days_taken: int


class ILeaveProvider(Protocol):
    """
    Interface for leave data exposed to other modules.

    Used by payroll module for calculating leave days.
    """

    def get_leave_balance(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalanceDTO | None:
        """Get leave balance for employee, type, and year."""
        ...

    def get_all_balances(
        self,
        employee_id: int,
        year: int,
    ) -> LeaveBalanceSummaryDTO:
        """Get all leave balances for employee in a year."""
        ...

    def get_leave_days_in_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """Get total approved leave days in a period."""
        ...

    def get_approved_leaves(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequestDTO]:
        """Get approved leave requests in a period."""
        ...

    def is_on_leave(
        self,
        employee_id: int,
        check_date: date,
    ) -> bool:
        """Check if employee is on approved leave on a specific date."""
        ...

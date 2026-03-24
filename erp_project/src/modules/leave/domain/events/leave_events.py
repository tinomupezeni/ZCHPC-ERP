"""
Leave domain events.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from shared.domain.base import DomainEvent


@dataclass(frozen=True)
class LeaveRequested(DomainEvent):
    """Event raised when a leave request is created."""

    request_id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    days: int

    @property
    def event_type(self) -> str:
        return "leave.requested"


@dataclass(frozen=True)
class LeaveApproved(DomainEvent):
    """Event raised when a leave request is approved."""

    request_id: int
    employee_id: int
    leave_type_id: int
    days: int
    approved_by_id: int
    approved_at: datetime

    @property
    def event_type(self) -> str:
        return "leave.approved"


@dataclass(frozen=True)
class LeaveRejected(DomainEvent):
    """Event raised when a leave request is rejected."""

    request_id: int
    employee_id: int
    rejected_by_id: int
    rejected_at: datetime

    @property
    def event_type(self) -> str:
        return "leave.rejected"


@dataclass(frozen=True)
class LeaveCancelled(DomainEvent):
    """Event raised when a leave request is cancelled."""

    request_id: int
    employee_id: int
    leave_type_id: int
    days: int
    was_approved: bool

    @property
    def event_type(self) -> str:
        return "leave.cancelled"


@dataclass(frozen=True)
class LeaveBalanceAdjusted(DomainEvent):
    """Event raised when a leave balance is adjusted."""

    balance_id: int
    employee_id: int
    leave_type_id: int
    year: int
    previous_remaining: Decimal
    new_remaining: Decimal
    adjustment_reason: str

    @property
    def event_type(self) -> str:
        return "leave.balance_adjusted"


@dataclass(frozen=True)
class LeaveTypeCreated(DomainEvent):
    """Event raised when a new leave type is created."""

    leave_type_id: int
    name: str
    default_days: int

    @property
    def event_type(self) -> str:
        return "leave.type_created"

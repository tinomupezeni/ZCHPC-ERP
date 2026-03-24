"""
Leave repository interfaces.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence

from modules.leave.domain.entities import LeaveBalance, LeaveRequest, LeaveType
from modules.leave.domain.value_objects import LeaveStatus


class ILeaveTypeRepository(ABC):
    """Interface for leave type repository."""

    @abstractmethod
    def get_by_id(self, leave_type_id: int) -> LeaveType | None:
        """Get leave type by ID."""
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> LeaveType | None:
        """Get leave type by name."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> Sequence[LeaveType]:
        """Get all leave types."""
        ...

    @abstractmethod
    def save(self, leave_type: LeaveType) -> LeaveType:
        """Save leave type."""
        ...

    @abstractmethod
    def delete(self, leave_type_id: int) -> None:
        """Delete leave type."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...


class ILeaveBalanceRepository(ABC):
    """Interface for leave balance repository."""

    @abstractmethod
    def get_by_id(self, balance_id: int) -> LeaveBalance | None:
        """Get balance by ID."""
        ...

    @abstractmethod
    def get_by_employee_and_type_and_year(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalance | None:
        """Get balance for employee, type, and year."""
        ...

    @abstractmethod
    def get_by_employee_and_year(
        self,
        employee_id: int,
        year: int,
    ) -> Sequence[LeaveBalance]:
        """Get all balances for employee in a year."""
        ...

    @abstractmethod
    def get_by_employee(self, employee_id: int) -> Sequence[LeaveBalance]:
        """Get all balances for employee."""
        ...

    @abstractmethod
    def save(self, balance: LeaveBalance) -> LeaveBalance:
        """Save balance."""
        ...

    @abstractmethod
    def delete(self, balance_id: int) -> None:
        """Delete balance."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...


class ILeaveRequestRepository(ABC):
    """Interface for leave request repository."""

    @abstractmethod
    def get_by_id(self, request_id: int) -> LeaveRequest | None:
        """Get request by ID."""
        ...

    @abstractmethod
    def get_by_employee(
        self,
        employee_id: int,
        year: int | None = None,
        status: LeaveStatus | None = None,
    ) -> Sequence[LeaveRequest]:
        """Get requests for employee with optional filters."""
        ...

    @abstractmethod
    def get_by_employee_and_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequest]:
        """Get requests for employee in a date range."""
        ...

    @abstractmethod
    def get_pending_requests(
        self,
        employee_id: int | None = None,
    ) -> Sequence[LeaveRequest]:
        """Get pending requests, optionally filtered by employee."""
        ...

    @abstractmethod
    def get_approved_requests_in_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequest]:
        """Get approved requests in a period."""
        ...

    @abstractmethod
    def save(self, request: LeaveRequest) -> LeaveRequest:
        """Save request."""
        ...

    @abstractmethod
    def delete(self, request_id: int) -> None:
        """Delete request."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...

"""
Domain events for employees.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from shared.domain.base import DomainEvent


@dataclass(frozen=True)
class EmployeeHiredEvent(DomainEvent):
    """Event raised when a new employee is hired."""

    employee_id: int
    employee_number: str
    first_name: str
    surname: str
    department_id: int | None
    position_id: int | None
    date_joined: date


@dataclass(frozen=True)
class EmployeeUpdatedEvent(DomainEvent):
    """Event raised when an employee's profile is updated."""

    employee_id: int
    employee_number: str
    changes: tuple[str, ...]


@dataclass(frozen=True)
class EmployeeTerminatedEvent(DomainEvent):
    """Event raised when an employee is terminated/deactivated."""

    employee_id: int
    employee_number: str
    reason: str = ""


@dataclass(frozen=True)
class EmployeeReactivatedEvent(DomainEvent):
    """Event raised when a terminated employee is reactivated."""

    employee_id: int
    employee_number: str


@dataclass(frozen=True)
class SalaryChangedEvent(DomainEvent):
    """Event raised when an employee's salary is changed."""

    employee_id: int
    employee_number: str
    old_usd_amount: Decimal | None
    old_zig_amount: Decimal | None
    new_usd_amount: Decimal
    new_zig_amount: Decimal


@dataclass(frozen=True)
class DepartmentChangedEvent(DomainEvent):
    """Event raised when an employee is moved to a different department."""

    employee_id: int
    employee_number: str
    old_department_id: int | None
    new_department_id: int


@dataclass(frozen=True)
class PositionChangedEvent(DomainEvent):
    """Event raised when an employee's position is changed."""

    employee_id: int
    employee_number: str
    old_position_id: int | None
    new_position_id: int


@dataclass(frozen=True)
class ContractUpdatedEvent(DomainEvent):
    """Event raised when an employee's contract dates are updated."""

    employee_id: int
    employee_number: str
    contract_from: date | None
    contract_to: date | None

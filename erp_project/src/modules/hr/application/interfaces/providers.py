"""
Provider interfaces exposed to other modules.

These interfaces define the contracts that other modules (Payroll, Leave, etc.)
use to access HR data without depending on HR internals.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class EmployeeDTO:
    """
    Data transfer object for employee information.

    This is the read-only view of an employee exposed to other modules.
    """

    id: int
    employee_id: str
    first_name: str
    surname: str
    full_name: str
    email: str | None
    department_id: int | None
    department_name: str | None
    position_id: int | None
    position_title: str | None
    date_joined: date
    is_active: bool


@dataclass(frozen=True)
class SalaryDTO:
    """
    Data transfer object for salary information.
    """

    employee_id: int
    employee_number: str
    usd_amount: Decimal
    zig_amount: Decimal
    pay_frequency: str


@dataclass(frozen=True)
class DepartmentDTO:
    """
    Data transfer object for department information.
    """

    id: int
    name: str
    description: str
    employee_count: int = 0


@dataclass(frozen=True)
class PositionDTO:
    """
    Data transfer object for position information.
    """

    id: int
    title: str
    department_id: int
    department_name: str
    description: str


class IEmployeeProvider(Protocol):
    """
    Interface for other modules to access employee data.

    This is the primary interface that modules like Payroll, Leave,
    and Attendance use to get employee information.
    """

    def get_employee(self, employee_id: int) -> EmployeeDTO | None:
        """Get employee by database ID."""
        ...

    def get_employee_by_employee_id(self, employee_id: str) -> EmployeeDTO | None:
        """Get employee by employee number (EMP0001)."""
        ...

    def get_active_employees(self) -> list[EmployeeDTO]:
        """Get all active employees."""
        ...

    def get_employees_by_department(self, department_id: int) -> list[EmployeeDTO]:
        """Get active employees in a department."""
        ...

    def get_employee_salary(self, employee_id: int) -> SalaryDTO | None:
        """Get employee's salary information."""
        ...

    def get_employees_for_payroll(self, department_id: int | None = None) -> list[EmployeeDTO]:
        """
        Get employees eligible for payroll processing.

        Args:
            department_id: Optional filter by department

        Returns:
            List of active employees for payroll
        """
        ...


class IDepartmentProvider(Protocol):
    """
    Interface for other modules to access department data.
    """

    def get_department(self, department_id: int) -> DepartmentDTO | None:
        """Get department by ID."""
        ...

    def get_all_departments(self) -> list[DepartmentDTO]:
        """Get all departments."""
        ...

    def get_department_by_name(self, name: str) -> DepartmentDTO | None:
        """Get department by name."""
        ...


class IPositionProvider(Protocol):
    """
    Interface for other modules to access position data.
    """

    def get_position(self, position_id: int) -> PositionDTO | None:
        """Get position by ID."""
        ...

    def get_positions_by_department(self, department_id: int) -> list[PositionDTO]:
        """Get positions in a department."""
        ...

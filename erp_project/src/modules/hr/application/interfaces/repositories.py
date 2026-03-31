"""
Repository interfaces for HR module.
"""

from abc import ABC, abstractmethod

from shared.domain.value_objects import EmployeeId

from modules.hr.domain.entities import Department, Employee, Position


class IEmployeeRepository(ABC):
    """
    Repository interface for Employee aggregate.
    """

    @abstractmethod
    def get_by_id(self, employee_id: int) -> Employee | None:
        """Get employee by database ID."""
        ...

    @abstractmethod
    def get_by_employee_id(self, employee_id: EmployeeId | str) -> Employee | None:
        """Get employee by employee number (EMP0001)."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Employee | None:
        """Get employee by email address."""
        ...

    @abstractmethod
    def get_by_national_id(self, national_id: str) -> Employee | None:
        """Get employee by national ID."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> list[Employee]:
        """Get all employees."""
        ...

    @abstractmethod
    def get_by_department(self, department_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees in a department."""
        ...

    @abstractmethod
    def get_by_position(self, position_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees with a specific position."""
        ...

    @abstractmethod
    def get_max_employee_id(self) -> EmployeeId | None:
        """Get the highest employee ID number."""
        ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if an employee with the given email exists."""
        ...

    @abstractmethod
    def exists_by_national_id(self, national_id: str) -> bool:
        """Check if an employee with the given national ID exists."""
        ...

    @abstractmethod
    def exists_by_employee_id(self, employee_id: str) -> bool:
        """Check if an employee with the given employee ID (EC Number) exists."""
        ...

    @abstractmethod
    def count(self, include_inactive: bool = False) -> int:
        """Count employees."""
        ...

    @abstractmethod
    def add(self, employee: Employee) -> None:
        """Add a new employee."""
        ...

    @abstractmethod
    def update(self, employee: Employee) -> None:
        """Update an existing employee."""
        ...

    @abstractmethod
    def delete(self, employee_id: int) -> bool:
        """Hard delete an employee. Returns True if deleted."""
        ...


class IDepartmentRepository(ABC):
    """
    Repository interface for Department aggregate.
    """

    @abstractmethod
    def get_by_id(self, department_id: int) -> Department | None:
        """Get department by ID."""
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> Department | None:
        """Get department by name."""
        ...

    @abstractmethod
    def get_all(self) -> list[Department]:
        """Get all departments."""
        ...

    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """Check if a department with the given name exists."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Count departments."""
        ...

    @abstractmethod
    def add(self, department: Department) -> None:
        """Add a new department."""
        ...

    @abstractmethod
    def update(self, department: Department) -> None:
        """Update an existing department."""
        ...

    @abstractmethod
    def delete(self, department_id: int) -> bool:
        """Delete a department. Returns True if deleted."""
        ...


class IPositionRepository(ABC):
    """
    Repository interface for Position aggregate.
    """

    @abstractmethod
    def get_by_id(self, position_id: int) -> Position | None:
        """Get position by ID."""
        ...

    @abstractmethod
    def get_by_title(self, title: str) -> Position | None:
        """Get position by title."""
        ...

    @abstractmethod
    def get_all(self) -> list[Position]:
        """Get all positions."""
        ...

    @abstractmethod
    def get_by_department(self, department_id: int) -> list[Position]:
        """Get positions in a department."""
        ...

    @abstractmethod
    def exists_by_title(self, title: str) -> bool:
        """Check if a position with the given title exists."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Count positions."""
        ...

    @abstractmethod
    def add(self, position: Position) -> None:
        """Add a new position."""
        ...

    @abstractmethod
    def update(self, position: Position) -> None:
        """Update an existing position."""
        ...

    @abstractmethod
    def delete(self, position_id: int) -> bool:
        """Delete a position. Returns True if deleted."""
        ...

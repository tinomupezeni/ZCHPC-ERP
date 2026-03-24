"""
HR application interfaces.
"""

from modules.hr.application.interfaces.providers import (
    DepartmentDTO,
    EmployeeDTO,
    IDepartmentProvider,
    IEmployeeProvider,
    IPositionProvider,
    PositionDTO,
    SalaryDTO,
)
from modules.hr.application.interfaces.repositories import (
    IDepartmentRepository,
    IEmployeeRepository,
    IPositionRepository,
)

__all__ = [
    # DTOs
    "EmployeeDTO",
    "SalaryDTO",
    "DepartmentDTO",
    "PositionDTO",
    # Providers (for other modules)
    "IEmployeeProvider",
    "IDepartmentProvider",
    "IPositionProvider",
    # Repositories (for internal use)
    "IEmployeeRepository",
    "IDepartmentRepository",
    "IPositionRepository",
]

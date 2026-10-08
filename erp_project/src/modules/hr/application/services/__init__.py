"""
HR application services.
"""

from modules.hr.application.services.employee_lifecycle_service import (
    EmployeeLifecycleService,
    LifecycleTransitionResult,
)
from modules.hr.application.services.employee_service import (
    CreateEmployeeCommand,
    EmployeeService,
    UpdateEmployeeCommand,
)
from modules.hr.application.services.organization_service import (
    CreateDepartmentCommand,
    CreatePositionCommand,
    DepartmentService,
    PositionService,
    UpdateDepartmentCommand,
    UpdatePositionCommand,
)
from modules.hr.application.services.role_service import (
    CreateRoleCommand,
    RoleService,
    UpdateRoleCommand,
)

__all__ = [
    # Employee service
    "EmployeeService",
    "CreateEmployeeCommand",
    "UpdateEmployeeCommand",
    # Employee lifecycle transitions
    "EmployeeLifecycleService",
    "LifecycleTransitionResult",
    # Department service
    "DepartmentService",
    "CreateDepartmentCommand",
    "UpdateDepartmentCommand",
    # Position service
    "PositionService",
    "CreatePositionCommand",
    "UpdatePositionCommand",
    # Role service
    "RoleService",
    "CreateRoleCommand",
    "UpdateRoleCommand",
]

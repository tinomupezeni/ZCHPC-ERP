"""
HR API views.
"""

from modules.hr.api.views.employee_views import (
    EmployeeDetailView,
    EmployeeListCreateView,
    EmployeeSalaryView,
)
from modules.hr.api.views.organization_views import (
    DepartmentDetailView,
    DepartmentListCreateView,
    PositionDetailView,
    PositionListCreateView,
    RoleDetailView,
    RoleListCreateView,
)

__all__ = [
    # Employee
    "EmployeeListCreateView",
    "EmployeeDetailView",
    "EmployeeSalaryView",
    # Department
    "DepartmentListCreateView",
    "DepartmentDetailView",
    # Position
    "PositionListCreateView",
    "PositionDetailView",
    # Role
    "RoleListCreateView",
    "RoleDetailView",
]

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
from modules.hr.api.views.dashboard_views import HRDashboardView
from modules.hr.api.views.payroll_config_views import (
    DeductionTypeListCreateView,
    DeductionTypeDetailView,
    AllowanceTypeListCreateView,
    AllowanceTypeDetailView,
)

__all__ = [
    # Dashboard
    "HRDashboardView",
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
    # Deductions & Allowances
    "DeductionTypeListCreateView",
    "DeductionTypeDetailView",
    "AllowanceTypeListCreateView",
    "AllowanceTypeDetailView",
]

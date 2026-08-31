"""
HR module URL configuration.

These URLs are mounted under /api/v2/hr/
"""

from django.urls import path

from modules.hr.api.views import (
    DepartmentDetailView,
    DepartmentListCreateView,
    DeductionTypeDetailView,
    DeductionTypeListCreateView,
    AllowanceTypeListCreateView,
    AllowanceTypeDetailView,
    EmployeeDetailView,
    EmployeeListCreateView,
    EmployeeSalaryView,
    EventDetailView,
    EventListCreateView,
    HRDashboardView,
    PositionDetailView,
    PositionListCreateView,
    RoleDetailView,
    RoleListCreateView,
)

app_name = "hr"

urlpatterns = [
    # Dashboard
    path("dashboard/", HRDashboardView.as_view(), name="hr_dashboard"),

    # Employees
    path("employees/", EmployeeListCreateView.as_view(), name="employee_list"),
    path("employees/<int:employee_id>/", EmployeeDetailView.as_view(), name="employee_detail"),
    path("employees/<int:employee_id>/salary/", EmployeeSalaryView.as_view(), name="employee_salary"),

    # Departments
    path("departments/", DepartmentListCreateView.as_view(), name="department_list"),
    path("departments/<int:department_id>/", DepartmentDetailView.as_view(), name="department_detail"),

    # Positions
    path("positions/", PositionListCreateView.as_view(), name="position_list"),
    path("positions/<int:position_id>/", PositionDetailView.as_view(), name="position_detail"),

    # Roles
    path("roles/", RoleListCreateView.as_view(), name="role_list"),
    path("roles/<int:role_id>/", RoleDetailView.as_view(), name="role_detail"),

    # Deductions
    path("deductions/", DeductionTypeListCreateView.as_view(), name="deduction_list"),
    path("deductions/<int:deduction_id>/", DeductionTypeDetailView.as_view(), name="deduction_detail"),

    # Allowances
    path("allowances/", AllowanceTypeListCreateView.as_view(), name="allowance_list"),
    path("allowances/<int:allowance_id>/", AllowanceTypeDetailView.as_view(), name="allowance_detail"),

    # Company calendar events
    path("events/", EventListCreateView.as_view(), name="event_list"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event_detail"),
]

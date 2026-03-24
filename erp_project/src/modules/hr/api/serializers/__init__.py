"""
HR API serializers.
"""

from modules.hr.api.serializers.employee_serializers import (
    CreateEmployeeRequestSerializer,
    EmployeeListItemSerializer,
    EmployeeResponseSerializer,
    SalarySerializer,
    UpdateEmployeeRequestSerializer,
)
from modules.hr.api.serializers.organization_serializers import (
    CreateDepartmentRequestSerializer,
    CreatePositionRequestSerializer,
    DepartmentResponseSerializer,
    PositionResponseSerializer,
    UpdateDepartmentRequestSerializer,
    UpdatePositionRequestSerializer,
)

__all__ = [
    # Employee
    "EmployeeResponseSerializer",
    "EmployeeListItemSerializer",
    "CreateEmployeeRequestSerializer",
    "UpdateEmployeeRequestSerializer",
    "SalarySerializer",
    # Department
    "DepartmentResponseSerializer",
    "CreateDepartmentRequestSerializer",
    "UpdateDepartmentRequestSerializer",
    # Position
    "PositionResponseSerializer",
    "CreatePositionRequestSerializer",
    "UpdatePositionRequestSerializer",
]

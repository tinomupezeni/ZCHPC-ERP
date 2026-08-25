"""
HR module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.hr.infrastructure.persistence.models import (
    AllowanceType,
    DeductionType,
    Department,
    Employees,
    Position,
    Role,
)

__all__ = [
    "Department",
    "Role",
    "Position",
    "Employees",
    "AllowanceType",
    "DeductionType",
]

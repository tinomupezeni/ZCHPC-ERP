"""
HR module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.hr.infrastructure.persistence.models import (
    Address,
    AllowanceType,
    DeductionType,
    Department,
    EmployeeAllowance,
    EmployeeDeduction,
    EmployeePayrollConfig,
    Employees,
    InsuranceOption,
    MedicalAidPlan,
    PensionFund,
    Position,
    Role,
    TrainingCertification,
    TrainingEnrollment,
    TrainingProgram,
    TrainingSession,
    Union,
)

__all__ = [
    "Department",
    "Role",
    "Position",
    "Address",
    "Employees",
    "AllowanceType",
    "DeductionType",
    "MedicalAidPlan",
    "PensionFund",
    "InsuranceOption",
    "Union",
    "EmployeeAllowance",
    "EmployeeDeduction",
    "EmployeePayrollConfig",
    "TrainingProgram",
    "TrainingSession",
    "TrainingEnrollment",
    "TrainingCertification",
]

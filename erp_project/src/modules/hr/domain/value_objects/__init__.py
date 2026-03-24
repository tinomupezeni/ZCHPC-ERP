"""
HR domain value objects.
"""

from modules.hr.domain.value_objects.employment import (
    BankAccount,
    EmploymentType,
    Gender,
    MaritalStatus,
    PayFrequency,
)
from modules.hr.domain.value_objects.salary import Salary
from modules.hr.domain.value_objects.statutory import (
    EmergencyContact,
    StatutoryInfo,
)

__all__ = [
    # Employment
    "EmploymentType",
    "PayFrequency",
    "Gender",
    "MaritalStatus",
    "BankAccount",
    # Salary
    "Salary",
    # Statutory
    "StatutoryInfo",
    "EmergencyContact",
]

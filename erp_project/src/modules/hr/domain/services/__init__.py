"""
HR domain services.
"""

from modules.hr.domain.services.employee_id_generator import (
    IEmployeeIdGenerator,
    SequentialEmployeeIdGenerator,
)

__all__ = [
    "IEmployeeIdGenerator",
    "SequentialEmployeeIdGenerator",
]

"""
Shared value objects used across modules.

Value objects are immutable and compared by their attributes.
They encapsulate validation logic for common domain concepts.
"""

from shared.domain.value_objects.date_range import DateRange
from shared.domain.value_objects.email import Email
from shared.domain.value_objects.employee_id import EmployeeId
from shared.domain.value_objects.money import Currency, Money
from shared.domain.value_objects.national_id import NationalId
from shared.domain.value_objects.period import Period
from shared.domain.value_objects.phone import PhoneNumber

__all__ = [
    "Money",
    "Currency",
    "DateRange",
    "Period",
    "Email",
    "PhoneNumber",
    "NationalId",
    "EmployeeId",
]

"""
Employee ID value object with generation and validation.

Handles employee identifiers in the format EMP0001, EMP0002, etc.

Example:
    emp_id = EmployeeId("EMP0001")
    next_id = EmployeeId.generate(current_max=1)  # EMP0002
"""

import re
from dataclasses import dataclass
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


@dataclass(frozen=True)
class EmployeeId(ValueObject):
    """
    Value object representing an employee identifier.

    Format: EMP followed by zero-padded number (EMP0001, EMP0002, etc.)

    Attributes:
        value: The employee ID string

    Usage:
        emp_id = EmployeeId("EMP0001")
        print(emp_id.numeric_part)  # 1

        # Generate next ID
        next_id = EmployeeId.generate(current_max=5)  # EMP0006
    """

    value: str

    # Employee ID pattern: EMP followed by digits
    EMPLOYEE_ID_PATTERN = re.compile(r"^EMP(\d{4,6})$", re.IGNORECASE)

    # Prefix for employee IDs
    PREFIX = "EMP"

    # Number of digits for padding
    PADDING = 4

    def __post_init__(self) -> None:
        """Validate and normalize employee ID on creation."""
        if not self.value:
            raise ValidationError(
                "Employee ID cannot be empty",
                code="EMPTY_EMPLOYEE_ID",
            )

        # Normalize: uppercase
        normalized = self.value.strip().upper()
        object.__setattr__(self, "value", normalized)

        # Validate format
        if not self.EMPLOYEE_ID_PATTERN.match(normalized):
            raise ValidationError(
                f"Invalid Employee ID format: {self.value}. Expected format: EMP0001",
                code="INVALID_EMPLOYEE_ID_FORMAT",
                details={"employee_id": self.value},
            )

    @classmethod
    def generate(cls, current_max: int = 0) -> "EmployeeId":
        """
        Generate the next employee ID.

        Args:
            current_max: The numeric part of the current highest ID

        Returns:
            New EmployeeId with incremented number
        """
        next_number = current_max + 1
        value = f"{cls.PREFIX}{next_number:0{cls.PADDING}d}"
        return cls(value=value)

    @classmethod
    def from_number(cls, number: int) -> "EmployeeId":
        """
        Create an employee ID from a number.

        Args:
            number: The numeric part of the ID

        Returns:
            EmployeeId with the specified number
        """
        if number < 1:
            raise ValidationError(
                "Employee ID number must be positive",
                code="INVALID_EMPLOYEE_NUMBER",
                details={"number": number},
            )
        value = f"{cls.PREFIX}{number:0{cls.PADDING}d}"
        return cls(value=value)

    @property
    def numeric_part(self) -> int:
        """Extract the numeric portion of the employee ID."""
        match = self.EMPLOYEE_ID_PATTERN.match(self.value)
        if match:
            return int(match.group(1))
        return 0

    def next(self) -> "EmployeeId":
        """Get the next sequential employee ID."""
        return EmployeeId.from_number(self.numeric_part + 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "numeric_part": self.numeric_part,
        }

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"EmployeeId(value={self.value!r})"

    def __lt__(self, other: "EmployeeId") -> bool:
        """Less than comparison based on numeric part."""
        return self.numeric_part < other.numeric_part

    def __le__(self, other: "EmployeeId") -> bool:
        """Less than or equal comparison."""
        return self.numeric_part <= other.numeric_part

    def __gt__(self, other: "EmployeeId") -> bool:
        """Greater than comparison."""
        return self.numeric_part > other.numeric_part

    def __ge__(self, other: "EmployeeId") -> bool:
        """Greater than or equal comparison."""
        return self.numeric_part >= other.numeric_part

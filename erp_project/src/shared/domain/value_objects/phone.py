"""
Phone number value object with validation.

Handles phone numbers with optional country code,
normalized for consistent storage and comparison.

Example:
    phone = PhoneNumber("+263 77 123 4567")
    print(phone.value)  # +263771234567
"""

import re
from dataclasses import dataclass
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """
    Value object representing a validated phone number.

    Phone numbers are normalized by removing spaces and dashes.
    Supports international format with country code.

    Attributes:
        value: The normalized phone number

    Usage:
        phone = PhoneNumber("+263 77 123 4567")
        phone = PhoneNumber("0771234567")  # Local format
        print(phone.value)  # Normalized format
    """

    value: str

    # Common Zimbabwe phone patterns
    # Mobile: 071, 073, 077, 078 (7 digits after prefix)
    # Landline: 024 (Harare), 029 (Bulawayo), etc.
    ZW_MOBILE_PATTERN = re.compile(r"^(\+263|0)(71|73|77|78)\d{7}$")
    ZW_LANDLINE_PATTERN = re.compile(r"^(\+263|0)(24|29|25|26|27)\d{6,7}$")

    def __post_init__(self) -> None:
        """Validate and normalize phone number on creation."""
        if not self.value:
            raise ValidationError(
                "Phone number cannot be empty",
                code="EMPTY_PHONE",
            )

        # Normalize: remove spaces, dashes, parentheses
        normalized = re.sub(r"[\s\-\(\)]+", "", self.value.strip())
        object.__setattr__(self, "value", normalized)

        # Basic validation: must contain only digits and optional leading +
        if not re.match(r"^\+?\d{7,15}$", normalized):
            raise ValidationError(
                f"Invalid phone number format: {self.value}",
                code="INVALID_PHONE_FORMAT",
                details={"phone": self.value},
            )

    @property
    def is_mobile(self) -> bool:
        """Check if this is a Zimbabwe mobile number."""
        return bool(self.ZW_MOBILE_PATTERN.match(self.value))

    @property
    def is_landline(self) -> bool:
        """Check if this is a Zimbabwe landline number."""
        return bool(self.ZW_LANDLINE_PATTERN.match(self.value))

    @property
    def is_international(self) -> bool:
        """Check if number has international prefix."""
        return self.value.startswith("+")

    def to_international(self, country_code: str = "+263") -> "PhoneNumber":
        """
        Convert to international format.

        Args:
            country_code: Country code to prepend (default: Zimbabwe +263)
        """
        if self.is_international:
            return self

        # Remove leading 0 and prepend country code
        if self.value.startswith("0"):
            return PhoneNumber(value=country_code + self.value[1:])

        return PhoneNumber(value=country_code + self.value)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"value": self.value}

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"PhoneNumber(value={self.value!r})"

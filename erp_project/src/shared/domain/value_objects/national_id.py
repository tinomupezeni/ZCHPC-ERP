"""
Zimbabwe National ID value object with validation.

Validates and normalizes Zimbabwe national ID numbers.

Example:
    nid = NationalId("63-123456-A-78")
    print(nid.value)  # 63-123456-A-78
"""

import re
from dataclasses import dataclass
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


@dataclass(frozen=True)
class NationalId(ValueObject):
    """
    Value object representing a Zimbabwe National ID.

    Zimbabwe National ID format: XX-NNNNNN-L-NN
    - XX: District code (2 digits)
    - NNNNNN: Serial number (6 digits)
    - L: Check letter (A-Z)
    - NN: Check digits (2 digits)

    Attributes:
        value: The normalized national ID string

    Usage:
        nid = NationalId("63-123456-A-78")
        print(nid.district_code)  # 63
        print(nid.serial_number)  # 123456
        print(nid.check_letter)  # A
    """

    value: str

    # Zimbabwe National ID pattern
    # Format: XX-NNNNNN-L-NN (e.g., 63-123456-A-78)
    NATIONAL_ID_PATTERN = re.compile(
        r"^(\d{2})-(\d{6,7})-([A-Z])-(\d{2})$",
        re.IGNORECASE
    )

    def __post_init__(self) -> None:
        """Validate and normalize national ID on creation."""
        if not self.value:
            raise ValidationError(
                "National ID cannot be empty",
                code="EMPTY_NATIONAL_ID",
            )

        # Normalize: uppercase and clean up
        normalized = self.value.strip().upper()

        # Replace spaces with dashes for normalization (handles "63-1670679 N 34" -> "63-1670679-N-34")
        normalized = normalized.replace(" ", "-")

        # Remove any double dashes that might have been created
        while "--" in normalized:
            normalized = normalized.replace("--", "-")

        # Try to add missing dashes if provided without them
        if "-" not in normalized and len(normalized) >= 11:
            # Attempt to format: XXNNNNNNLNN -> XX-NNNNNN-L-NN
            normalized = f"{normalized[:2]}-{normalized[2:8]}-{normalized[8]}-{normalized[9:]}"

        object.__setattr__(self, "value", normalized)

        # Validate format
        if not self.NATIONAL_ID_PATTERN.match(normalized):
            raise ValidationError(
                f"Invalid National ID format: {self.value}. Expected format: XX-NNNNNN-L-NN",
                code="INVALID_NATIONAL_ID_FORMAT",
                details={"national_id": self.value},
            )

    @property
    def district_code(self) -> str:
        """The district code (first 2 digits)."""
        return self.value.split("-")[0]

    @property
    def serial_number(self) -> str:
        """The serial number (6 digits after district code)."""
        return self.value.split("-")[1]

    @property
    def check_letter(self) -> str:
        """The check letter."""
        return self.value.split("-")[2]

    @property
    def check_digits(self) -> str:
        """The check digits (last 2 digits)."""
        return self.value.split("-")[3]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"value": self.value}

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"NationalId(value={self.value!r})"

"""
Email value object with validation.

Ensures email addresses are properly formatted and normalized.

Example:
    email = Email("User@Example.COM")
    print(email.value)  # user@example.com (normalized)
"""

import re
from dataclasses import dataclass
from typing import Any

from shared.domain.base.value_object import ValueObject
from shared.domain.exceptions import ValidationError


# RFC 5322 compliant email regex (simplified for practical use)
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


@dataclass(frozen=True)
class Email(ValueObject):
    """
    Value object representing a validated email address.

    Emails are normalized to lowercase for consistent comparison.

    Attributes:
        value: The normalized email address

    Usage:
        email = Email("User@Example.com")
        print(email.value)  # user@example.com
        print(email.domain)  # example.com
        print(email.local_part)  # user
    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize email on creation."""
        if not self.value:
            raise ValidationError(
                "Email cannot be empty",
                code="EMPTY_EMAIL",
            )

        # Normalize to lowercase
        normalized = self.value.strip().lower()
        object.__setattr__(self, "value", normalized)

        # Validate format
        if not EMAIL_PATTERN.match(normalized):
            raise ValidationError(
                f"Invalid email format: {self.value}",
                code="INVALID_EMAIL_FORMAT",
                details={"email": self.value},
            )

    @property
    def domain(self) -> str:
        """The domain part of the email (after @)."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """The local part of the email (before @)."""
        return self.value.split("@")[0]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"value": self.value}

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Email(value={self.value!r})"

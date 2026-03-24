"""
Password-related value objects.

Handles password hashing and validation securely.
"""

from dataclasses import dataclass
from typing import Any

from django.contrib.auth.hashers import check_password, make_password

from shared.domain.base import ValueObject
from shared.domain.exceptions import ValidationError


@dataclass(frozen=True)
class HashedPassword(ValueObject):
    """
    Value object representing a securely hashed password.

    Never stores plain text passwords. Uses Django's password hashing.

    Attributes:
        value: The hashed password string

    Usage:
        # Create from plain text
        hashed = HashedPassword.from_plain_text("mypassword123")

        # Verify password
        if hashed.verify("mypassword123"):
            print("Password correct!")
    """

    value: str

    @classmethod
    def from_plain_text(cls, plain_password: str) -> "HashedPassword":
        """
        Create a HashedPassword from plain text.

        Args:
            plain_password: The plain text password to hash

        Returns:
            HashedPassword with the hashed value

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        cls._validate_password_strength(plain_password)
        hashed = make_password(plain_password)
        return cls(value=hashed)

    @classmethod
    def from_hash(cls, hashed_password: str) -> "HashedPassword":
        """
        Create a HashedPassword from an existing hash.

        Use when loading from database.

        Args:
            hashed_password: The already-hashed password string
        """
        return cls(value=hashed_password)

    def verify(self, plain_password: str) -> bool:
        """
        Verify a plain text password against this hash.

        Args:
            plain_password: The plain text password to check

        Returns:
            True if password matches, False otherwise
        """
        return check_password(plain_password, self.value)

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        """
        Validate password meets minimum requirements.

        Args:
            password: Plain text password to validate

        Raises:
            ValidationError: If password is too weak
        """
        if not password:
            raise ValidationError(
                "Password cannot be empty",
                code="EMPTY_PASSWORD",
            )

        if len(password) < 8:
            raise ValidationError(
                "Password must be at least 8 characters",
                code="PASSWORD_TOO_SHORT",
                details={"min_length": 8, "actual_length": len(password)},
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excludes hash for security)."""
        return {"is_set": bool(self.value)}

    def __str__(self) -> str:
        """Never expose the hash in string representation."""
        return "HashedPassword(***)"

    def __repr__(self) -> str:
        """Never expose the hash in repr."""
        return "HashedPassword(value=***)"

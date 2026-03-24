"""
QR Token domain services.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from modules.attendance.domain.entities import QRToken
from modules.attendance.domain.value_objects import TokenExpiry, TokenValue


class IQRTokenGenerator(ABC):
    """Interface for QR token generation."""

    @abstractmethod
    def generate(
        self,
        validity_seconds: int = 30,
        created_at: datetime | None = None,
    ) -> tuple[TokenValue, TokenExpiry]:
        """
        Generate a new token with expiry.

        Args:
            validity_seconds: How long the token should be valid
            created_at: Creation timestamp (defaults to now)

        Returns:
            Tuple of (TokenValue, TokenExpiry)
        """
        ...


class IQRTokenValidator(ABC):
    """Interface for QR token validation."""

    @abstractmethod
    def validate(self, token_string: str) -> bool:
        """
        Validate a token string.

        Args:
            token_string: The token to validate

        Returns:
            True if valid, False otherwise
        """
        ...


class QRTokenGenerator(IQRTokenGenerator):
    """
    Default QR token generator.

    Generates cryptographically secure tokens with configurable validity.
    """

    def __init__(
        self,
        default_validity_seconds: int = 30,
        token_length: int = 32,
    ):
        """
        Initialize generator.

        Args:
            default_validity_seconds: Default token validity period
            token_length: Length of generated tokens
        """
        if default_validity_seconds <= 0:
            raise ValueError("Validity seconds must be positive")
        if token_length < 16:
            raise ValueError("Token length must be at least 16")

        self.default_validity_seconds = default_validity_seconds
        self.token_length = token_length

    def generate(
        self,
        validity_seconds: int | None = None,
        created_at: datetime | None = None,
    ) -> tuple[TokenValue, TokenExpiry]:
        """Generate a new token with expiry."""
        validity = validity_seconds or self.default_validity_seconds
        token = TokenValue.generate(length=self.token_length)
        expiry = TokenExpiry.create(
            validity_seconds=validity,
            created_at=created_at,
        )
        return token, expiry


class QRTokenValidator:
    """
    QR token validator.

    Validates tokens against active tokens.
    """

    def validate(
        self,
        token_string: str,
        active_token: QRToken | None,
        at_time: datetime | None = None,
    ) -> bool:
        """
        Validate a token string against the active token.

        Args:
            token_string: The token string to validate
            active_token: The currently active QR token
            at_time: Time to check validity at

        Returns:
            True if token is valid
        """
        if not active_token:
            return False

        return active_token.verify(token_string, at_time)

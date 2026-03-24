"""
QR Token value objects.
"""

import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta

from shared.domain.base import ValueObject


@dataclass(frozen=True)
class TokenValue(ValueObject):
    """
    QR token value.

    Represents the cryptographically secure token string.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate token."""
        if not self.value:
            raise ValueError("Token value cannot be empty")
        if len(self.value) < 16:
            raise ValueError("Token must be at least 16 characters")
        if len(self.value) > 64:
            raise ValueError("Token cannot exceed 64 characters")

    @classmethod
    def generate(cls, length: int = 32) -> "TokenValue":
        """Generate a cryptographically secure random token."""
        if length < 16:
            raise ValueError("Token length must be at least 16")
        if length > 64:
            raise ValueError("Token length cannot exceed 64")

        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for _ in range(length))
        return cls(value=token)

    @property
    def masked(self) -> str:
        """Get masked version for display (first 8 chars only)."""
        return f"{self.value[:8]}..."

    def __str__(self) -> str:
        """String representation (masked for security)."""
        return self.masked


@dataclass(frozen=True)
class TokenExpiry(ValueObject):
    """
    Token expiry configuration.

    Defines when a token expires.
    """

    created_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        """Validate expiry times."""
        if self.expires_at <= self.created_at:
            raise ValueError("Expiry time must be after creation time")

    @classmethod
    def create(
        cls, validity_seconds: int = 30, created_at: datetime | None = None
    ) -> "TokenExpiry":
        """Create token expiry with given validity period."""
        if validity_seconds <= 0:
            raise ValueError("Validity seconds must be positive")
        if validity_seconds > 3600:
            raise ValueError("Validity cannot exceed 1 hour")

        now = created_at or datetime.utcnow()
        return cls(
            created_at=now,
            expires_at=now + timedelta(seconds=validity_seconds),
        )

    @property
    def validity_seconds(self) -> int:
        """Get the validity period in seconds."""
        delta = self.expires_at - self.created_at
        return int(delta.total_seconds())

    def is_valid(self, at_time: datetime | None = None) -> bool:
        """Check if token is still valid."""
        check_time = at_time or datetime.utcnow()
        return check_time < self.expires_at

    @property
    def seconds_remaining(self) -> int:
        """Get seconds remaining until expiry."""
        now = datetime.utcnow()
        if now >= self.expires_at:
            return 0
        delta = self.expires_at - now
        return int(delta.total_seconds())

    def __str__(self) -> str:
        """String representation."""
        return f"Valid until {self.expires_at.isoformat()}"

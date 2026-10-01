"""
QRToken aggregate root.
"""

from datetime import datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.attendance.domain.value_objects import TokenExpiry, TokenValue


class QRToken(AggregateRoot[int]):
    """
    QRToken aggregate root.

    Represents a dynamic QR token for attendance clock-in.
    Tokens rotate every 30 seconds to prevent fraud.
    """

    DEFAULT_VALIDITY_SECONDS = 30
    MAX_VALIDITY_SECONDS = 3600  # 1 hour max

    def __init__(
        self,
        id: int,
        token: TokenValue,
        expiry: TokenExpiry,
        is_active: bool = True,
        used_count: int = 0,
    ):
        """Initialize QR token."""
        super().__init__(id)
        self.token = token
        self.expiry = expiry
        self.is_active = is_active
        self.used_count = used_count
        self._validate()

    def _validate(self) -> None:
        """Validate QR token."""
        if self.used_count < 0:
            raise ValidationError(
                message="Used count cannot be negative",
                code="INVALID_USED_COUNT",
            )

    @classmethod
    def create(
        cls,
        id: int,
        validity_seconds: int = DEFAULT_VALIDITY_SECONDS,
        created_at: datetime | None = None,
    ) -> "QRToken":
        """
        Create a new QR token.

        Args:
            id: Token ID
            validity_seconds: How long the token is valid (default 30 seconds)
            created_at: When the token was created (defaults to now)

        Returns:
            New QRToken instance
        """
        token = TokenValue.generate()
        expiry = TokenExpiry.create(
            validity_seconds=validity_seconds,
            created_at=created_at,
        )
        return cls(
            id=id,
            token=token,
            expiry=expiry,
            is_active=True,
            used_count=0,
        )

    @property
    def token_value(self) -> str:
        """Get the raw token string."""
        return self.token.value

    @property
    def created_at(self) -> datetime:
        """Get creation time."""
        return self.expiry.created_at

    @property
    def expires_at(self) -> datetime:
        """Get expiration time."""
        return self.expiry.expires_at

    @property
    def seconds_remaining(self) -> int:
        """Get seconds until expiration."""
        return self.expiry.seconds_remaining

    def is_valid(self, at_time: datetime | None = None) -> bool:
        """
        Check if token is valid.

        Args:
            at_time: Time to check validity at (defaults to now)

        Returns:
            True if token is active and not expired
        """
        if not self.is_active:
            return False
        return self.expiry.is_valid(at_time)

    def verify(self, token_string: str, at_time: datetime | None = None) -> bool:
        """
        Verify if a given token string matches this token.

        Args:
            token_string: The token string to verify
            at_time: Time to check validity at (defaults to now)

        Returns:
            True if token matches and is valid
        """
        if token_string != self.token.value:
            return False
        return self.is_valid(at_time)

    def increment_usage(self) -> int:
        """
        Increment the usage counter.

        Returns:
            The new usage count
        """
        self.used_count += 1
        return self.used_count

    def deactivate(self) -> None:
        """Deactivate this token."""
        self.is_active = False

    def __str__(self) -> str:
        """String representation."""
        status = "Active" if self.is_valid() else "Expired"
        return f"QRToken({self.token.masked}, {status})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"QRToken(id={self.id}, token={self.token.masked}, "
            f"is_active={self.is_active}, used_count={self.used_count})"
        )

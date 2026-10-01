"""
QR Token application service.
"""

from dataclasses import dataclass
from datetime import datetime

from shared.infrastructure.event_bus import EventBus

from modules.attendance.application.interfaces import IQRTokenRepository, QRTokenDTO
from modules.attendance.domain.entities import QRToken
from modules.attendance.domain.events import QRTokenGenerated, QRTokenUsed
from modules.attendance.domain.services import QRTokenGenerator, QRTokenValidator


@dataclass
class VerifyTokenCommand:
    """Command for verifying a QR token."""

    token_string: str
    employee_id: int


class QRTokenService:
    """
    Application service for QR token operations.

    Manages QR token lifecycle for attendance clock-in.
    """

    DEFAULT_VALIDITY_SECONDS = 30

    def __init__(
        self,
        token_repo: IQRTokenRepository,
        event_bus: EventBus | None = None,
        token_generator: QRTokenGenerator | None = None,
        token_validator: QRTokenValidator | None = None,
        validity_seconds: int = DEFAULT_VALIDITY_SECONDS,
    ):
        """
        Initialize service.

        Args:
            token_repo: QR token repository
            event_bus: Event bus for publishing domain events
            token_generator: Token generator
            token_validator: Token validator
            validity_seconds: Token validity period
        """
        self.token_repo = token_repo
        self.event_bus = event_bus
        self.token_generator = token_generator or QRTokenGenerator(validity_seconds)
        self.token_validator = token_validator or QRTokenValidator()
        self.validity_seconds = validity_seconds

    def get_or_create_current_token(self) -> QRTokenDTO:
        """
        Get the current valid token or create a new one.

        This is the main endpoint for QR displays - they poll this
        to get the current token to display.

        Returns:
            QRTokenDTO with current token info
        """
        # Try to get existing active token
        current = self.token_repo.get_current_active()

        if current and current.is_valid():
            return self._to_dto(current)

        # Deactivate all old tokens
        self.token_repo.deactivate_all()

        # Create new token
        token = QRToken.create(
            id=self.token_repo.get_next_id(),
            validity_seconds=self.validity_seconds,
        )
        token = self.token_repo.save(token)

        # Publish event
        if self.event_bus:
            event = QRTokenGenerated(
                token_id=token.id,
                expires_at=token.expires_at,
            )
            self.event_bus.publish(event)

        return self._to_dto(token)

    def verify_token(self, command: VerifyTokenCommand) -> bool:
        """
        Verify a scanned QR token.

        Args:
            command: Verification command with token string

        Returns:
            True if token is valid
        """
        active_token = self.token_repo.get_current_active()

        if not active_token:
            return False

        is_valid = self.token_validator.validate(
            command.token_string,
            active_token,
        )

        if is_valid:
            # Increment usage count
            active_token.increment_usage()
            self.token_repo.save(active_token)

            # Publish event
            if self.event_bus:
                event = QRTokenUsed(
                    token_id=active_token.id,
                    employee_id=command.employee_id,
                    used_at=datetime.utcnow(),
                )
                self.event_bus.publish(event)

        return is_valid

    def get_token_by_value(self, token_string: str) -> QRToken | None:
        """
        Get token by its string value.

        Args:
            token_string: The token string

        Returns:
            QRToken if found
        """
        return self.token_repo.get_by_token_value(token_string)

    def _to_dto(self, token: QRToken) -> QRTokenDTO:
        """Convert entity to DTO."""
        return QRTokenDTO(
            token=token.token_value,
            expires_at=token.expires_at,
            seconds_remaining=token.seconds_remaining,
        )

"""
Django ORM implementation of QR token repository.
"""

from datetime import datetime
from typing import Type

from django.utils import timezone

from modules.attendance.application.interfaces import IQRTokenRepository
from modules.attendance.domain.entities import QRToken
from modules.attendance.domain.value_objects import TokenExpiry, TokenValue


class DjangoQRTokenRepository(IQRTokenRepository):
    """
    Django ORM implementation of QR token repository.

    Maps QRToken domain entity to Django ORM model.
    """

    def __init__(self) -> None:
        """Initialize repository."""
        self._model: Type | None = None

    @property
    def model(self):
        """Lazy load the Django model to avoid circular imports."""
        if self._model is None:
            from employee_portal.models import AttendanceQRToken

            self._model = AttendanceQRToken
        return self._model

    def get_by_id(self, token_id: int) -> QRToken | None:
        """Get QR token by ID."""
        try:
            db_token = self.model.objects.get(pk=token_id)
            return self._to_entity(db_token)
        except self.model.DoesNotExist:
            return None

    def get_by_token_value(self, token_value: str) -> QRToken | None:
        """Get QR token by token string."""
        try:
            db_token = self.model.objects.get(token=token_value)
            return self._to_entity(db_token)
        except self.model.DoesNotExist:
            return None

    def get_current_active(self) -> QRToken | None:
        """Get the currently active (non-expired) token."""
        now = timezone.now()
        db_token = (
            self.model.objects.filter(
                is_active=True,
                expires_at__gt=now,
            )
            .order_by("-created_at")
            .first()
        )

        if db_token:
            return self._to_entity(db_token)
        return None

    def save(self, token: QRToken) -> QRToken:
        """Save QR token."""
        if token.id:
            # Update existing
            updated = self.model.objects.filter(pk=token.id).update(
                token=token.token_value,
                expires_at=token.expires_at,
                is_active=token.is_active,
                used_count=token.used_count,
            )
            if updated == 0:
                # Token doesn't exist, create it
                db_token = self.model.objects.create(
                    token=token.token_value,
                    expires_at=token.expires_at,
                    is_active=token.is_active,
                    used_count=token.used_count,
                )
                token = self._to_entity(db_token)
        else:
            # Create new
            db_token = self.model.objects.create(
                token=token.token_value,
                expires_at=token.expires_at,
                is_active=token.is_active,
                used_count=token.used_count,
            )
            token = self._to_entity(db_token)

        return token

    def deactivate_all(self) -> int:
        """Deactivate all active tokens."""
        return self.model.objects.filter(is_active=True).update(is_active=False)

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = self.model.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, db_token) -> QRToken:
        """Convert Django model to domain entity."""
        # Convert timezone-aware datetime to naive UTC
        created_at = db_token.created_at
        expires_at = db_token.expires_at

        if hasattr(created_at, "tzinfo") and created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        token_value = TokenValue(value=db_token.token)
        token_expiry = TokenExpiry(
            created_at=created_at,
            expires_at=expires_at,
        )

        return QRToken(
            id=db_token.id,
            token=token_value,
            expiry=token_expiry,
            is_active=db_token.is_active,
            used_count=db_token.used_count,
        )

"""
Django repository implementation for AuditLogEntry.
"""

from uuid import UUID

from django.db import transaction
from django.db.models import Q

from modules.identity.application.interfaces import IAuditLogRepository
from modules.identity.domain.entities import AuditEventType, AuditLogEntry


class DjangoAuditLogRepository(IAuditLogRepository):
    """
    Django ORM implementation of IAuditLogRepository.

    Maps between AuditLogEntry domain entity and Django's AuditLog model.
    Note: Only add operations are supported - audit logs are immutable.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of AuditLog model to avoid circular imports."""
        if self._model is None:
            from modules.identity.infrastructure.persistence.models import AuditLog
            self._model = AuditLog
        return self._model

    @transaction.atomic
    def add(self, entry: AuditLogEntry) -> AuditLogEntry:
        """
        Add a new audit log entry.

        Returns the entry with ID populated.
        """
        db_entry = self.model(
            user_id=entry.user_id,
            username_attempted=entry.username_attempted,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            event_type=entry.event_type.value,
        )
        db_entry.save()

        # Return new entry with ID
        return AuditLogEntry(
            id=db_entry.id,
            user_id=entry.user_id,
            username_attempted=entry.username_attempted,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            event_type=entry.event_type,
            timestamp=db_entry.timestamp,
            details=entry.details,
            _is_persisted=True,
        )

    def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """Get audit entries for a specific user."""
        queryset = (
            self.model.objects
            .filter(user_id=user_id)
            .order_by("-timestamp")[offset:offset + limit]
        )
        return [self._to_entity(e) for e in queryset]

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
    ) -> list[AuditLogEntry]:
        """Get all audit entries with optional filtering."""
        queryset = self.model.objects.all().order_by("-timestamp")

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        queryset = queryset[offset:offset + limit]
        return [self._to_entity(e) for e in queryset]

    def search(
        self,
        username: str | None = None,
        ip_address: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """Search audit entries by various criteria."""
        queryset = self.model.objects.all()

        if username:
            queryset = queryset.filter(username_attempted__icontains=username)

        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        queryset = queryset.order_by("-timestamp")[offset:offset + limit]
        return [self._to_entity(e) for e in queryset]

    def count(self, event_type: str | None = None) -> int:
        """Count audit entries, optionally filtered by event type."""
        queryset = self.model.objects.all()

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset.count()

    def _to_entity(self, db_entry) -> AuditLogEntry:
        """Convert Django model to domain entity."""
        return AuditLogEntry(
            id=db_entry.id,
            user_id=db_entry.user_id,
            username_attempted=db_entry.username_attempted,
            ip_address=db_entry.ip_address,
            user_agent=db_entry.user_agent,
            event_type=AuditEventType(db_entry.event_type),
            timestamp=db_entry.timestamp,
            details={},
            _is_persisted=True,
        )

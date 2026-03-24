"""
Django repository implementation for Position aggregate.
"""

from django.db import transaction

from modules.hr.application.interfaces import IPositionRepository
from modules.hr.domain.entities import Position


class DjangoPositionRepository(IPositionRepository):
    """
    Django ORM implementation of IPositionRepository.

    Maps between Position domain entity and Django's Position model.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of Position model to avoid circular imports."""
        if self._model is None:
            from modules.hr.infrastructure.persistence.models import Position as PositionModel
            self._model = PositionModel
        return self._model

    def get_by_id(self, position_id: int) -> Position | None:
        """Get position by ID."""
        try:
            db_pos = self.model.objects.select_related("department").get(id=position_id)
            return self._to_entity(db_pos)
        except self.model.DoesNotExist:
            return None

    def get_by_title(self, title: str) -> Position | None:
        """Get position by title."""
        try:
            db_pos = self.model.objects.select_related("department").get(title__iexact=title)
            return self._to_entity(db_pos)
        except self.model.DoesNotExist:
            return None

    def get_all(self) -> list[Position]:
        """Get all positions."""
        return [
            self._to_entity(p)
            for p in self.model.objects.select_related("department").all()
        ]

    def get_by_department(self, department_id: int) -> list[Position]:
        """Get positions in a department."""
        return [
            self._to_entity(p)
            for p in self.model.objects.select_related("department").filter(
                department_id=department_id
            )
        ]

    def exists_by_title(self, title: str) -> bool:
        """Check if a position with the given title exists."""
        return self.model.objects.filter(title__iexact=title).exists()

    def count(self) -> int:
        """Count positions."""
        return self.model.objects.count()

    @transaction.atomic
    def add(self, position: Position) -> None:
        """Add a new position."""
        db_pos = self.model(
            title=position.title,
            department_id=position.department_id,
            description=position.description or "",
        )
        db_pos.save()
        # Update the entity with the generated ID (set _id, not id property)
        object.__setattr__(position, "_id", db_pos.id)

    @transaction.atomic
    def update(self, position: Position) -> None:
        """Update an existing position."""
        self.model.objects.filter(id=position.id).update(
            title=position.title,
            department_id=position.department_id,
            description=position.description or "",
        )

    @transaction.atomic
    def delete(self, position_id: int) -> bool:
        """Delete a position. Returns True if deleted."""
        deleted, _ = self.model.objects.filter(id=position_id).delete()
        return deleted > 0

    def _to_entity(self, db_pos) -> Position:
        """Convert Django model to domain entity."""
        return Position(
            id=db_pos.id,
            title=db_pos.title,
            department_id=db_pos.department_id,
            description=db_pos.description or "",
        )

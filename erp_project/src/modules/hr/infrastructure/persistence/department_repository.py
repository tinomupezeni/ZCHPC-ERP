"""
Django repository implementation for Department aggregate.
"""

from django.db import transaction

from modules.hr.application.interfaces import IDepartmentRepository
from modules.hr.domain.entities import Department


class DjangoDepartmentRepository(IDepartmentRepository):
    """
    Django ORM implementation of IDepartmentRepository.

    Maps between Department domain entity and Django's Department model.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of Department model to avoid circular imports."""
        if self._model is None:
            from modules.hr.infrastructure.persistence.models import Department as DepartmentModel
            self._model = DepartmentModel
        return self._model

    def get_by_id(self, department_id: int) -> Department | None:
        """Get department by ID."""
        try:
            db_dept = self.model.objects.get(id=department_id)
            return self._to_entity(db_dept)
        except self.model.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Department | None:
        """Get department by name."""
        try:
            db_dept = self.model.objects.get(name__iexact=name)
            return self._to_entity(db_dept)
        except self.model.DoesNotExist:
            return None

    def get_all(self) -> list[Department]:
        """Get all departments."""
        return [self._to_entity(d) for d in self.model.objects.all()]

    def exists_by_name(self, name: str) -> bool:
        """Check if a department with the given name exists."""
        return self.model.objects.filter(name__iexact=name).exists()

    def count(self) -> int:
        """Count departments."""
        return self.model.objects.count()

    @transaction.atomic
    def add(self, department: Department) -> None:
        """Add a new department."""
        db_dept = self.model(
            name=department.name,
            description=department.description or "",
        )
        db_dept.save()
        # Update the entity with the generated ID (set _id, not id property)
        object.__setattr__(department, "_id", db_dept.id)

    @transaction.atomic
    def update(self, department: Department) -> None:
        """Update an existing department."""
        self.model.objects.filter(id=department.id).update(
            name=department.name,
            description=department.description or "",
        )

    @transaction.atomic
    def delete(self, department_id: int) -> bool:
        """Delete a department. Returns True if deleted."""
        deleted, _ = self.model.objects.filter(id=department_id).delete()
        return deleted > 0

    def _to_entity(self, db_dept) -> Department:
        """Convert Django model to domain entity."""
        return Department(
            id=db_dept.id,
            name=db_dept.name,
            description=db_dept.description or "",
        )

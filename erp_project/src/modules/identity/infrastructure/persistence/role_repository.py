"""
Django repository implementation for Role aggregate.
"""

from django.db import transaction

from modules.identity.application.interfaces import IRoleRepository
from modules.identity.domain.entities import Role
from modules.identity.domain.value_objects import PermissionSet


class DjangoRoleRepository(IRoleRepository):
    """
    Django ORM implementation of IRoleRepository.

    Maps between Role domain entity and Django's Role model.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of Role model to avoid circular imports."""
        if self._model is None:
            from modules.hr.infrastructure.persistence.models import Role as RoleModel
            self._model = RoleModel
        return self._model

    def get_by_id(self, role_id: int) -> Role | None:
        """Get role by ID."""
        try:
            db_role = self.model.objects.get(id=role_id)
            return self._to_entity(db_role)
        except self.model.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        try:
            db_role = self.model.objects.get(name__iexact=name)
            return self._to_entity(db_role)
        except self.model.DoesNotExist:
            return None

    def get_all(self) -> list[Role]:
        """Get all roles."""
        return [self._to_entity(r) for r in self.model.objects.all()]

    @transaction.atomic
    def add(self, role: Role) -> None:
        """Add a new role."""
        db_role = self.model(
            id=role.id if role.id else None,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions.to_list(),
        )
        db_role.save()

    @transaction.atomic
    def update(self, role: Role) -> None:
        """Update an existing role."""
        self.model.objects.filter(id=role.id).update(
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions.to_list(),
        )

    def _to_entity(self, db_role) -> Role:
        """Convert Django model to domain entity."""
        permissions = db_role.permissions if db_role.permissions else []
        return Role(
            id=db_role.id,
            name=db_role.name,
            display_name=db_role.display_name,
            description=db_role.description or "",
            permissions=PermissionSet.from_list(permissions),
        )

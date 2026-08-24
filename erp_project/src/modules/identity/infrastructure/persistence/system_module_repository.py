"""
Django repository implementation for SystemModule aggregate.
"""

from django.db import transaction
from modules.identity.application.interfaces import ISystemModuleRepository
from modules.identity.domain.entities import SystemModule


class DjangoSystemModuleRepository(ISystemModuleRepository):
    """
    Django ORM implementation of ISystemModuleRepository.
    """

    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from modules.identity.infrastructure.persistence.models import SystemModule as SystemModuleModel
            self._model = SystemModuleModel
        return self._model

    def get_by_id(self, module_id: int) -> SystemModule | None:
        try:
            db_module = self.model.objects.get(id=module_id)
            return self._to_entity(db_module)
        except self.model.DoesNotExist:
            return None

    def get_by_identifier(self, identifier: str) -> SystemModule | None:
        try:
            db_module = self.model.objects.get(identifier__iexact=identifier)
            return self._to_entity(db_module)
        except self.model.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = True) -> list[SystemModule]:
        queryset = self.model.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(m) for m in queryset]

    def get_active(self) -> list[SystemModule]:
        return self.get_all(include_inactive=False)

    @transaction.atomic
    def add(self, module: SystemModule) -> None:
        db_module = self.model(
            identifier=module.identifier,
            name=module.name,
            description=module.description,
            is_active=module.is_active,
            dependencies=module.dependencies,
        )
        db_module.save()
        module.id = db_module.id

    @transaction.atomic
    def update(self, module: SystemModule) -> None:
        self.model.objects.filter(id=module.id).update(
            identifier=module.identifier,
            name=module.name,
            description=module.description,
            is_active=module.is_active,
            dependencies=module.dependencies,
        )

    def _to_entity(self, db_module) -> SystemModule:
        return SystemModule(
            id=db_module.id,
            identifier=db_module.identifier,
            name=db_module.name,
            description=db_module.description or "",
            is_active=db_module.is_active,
            dependencies=db_module.dependencies or [],
        )

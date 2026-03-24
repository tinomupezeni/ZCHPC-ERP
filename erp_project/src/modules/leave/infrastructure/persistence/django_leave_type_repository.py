"""
Django ORM implementation of ILeaveTypeRepository.
"""

from typing import Sequence

from modules.leave.infrastructure.persistence.models import LeaveType as LeaveTypeModel

from modules.leave.application.interfaces import ILeaveTypeRepository
from modules.leave.domain.entities import LeaveType


class DjangoLeaveTypeRepository(ILeaveTypeRepository):
    """Django ORM implementation of leave type repository."""

    def get_by_id(self, leave_type_id: int) -> LeaveType | None:
        """Get leave type by ID."""
        try:
            model = LeaveTypeModel.objects.get(id=leave_type_id)
            return self._to_entity(model)
        except LeaveTypeModel.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> LeaveType | None:
        """Get leave type by name."""
        try:
            model = LeaveTypeModel.objects.get(name=name)
            return self._to_entity(model)
        except LeaveTypeModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> Sequence[LeaveType]:
        """Get all leave types."""
        # Note: Current model doesn't have is_active field
        # All leave types are considered active
        queryset = LeaveTypeModel.objects.all()
        return [self._to_entity(model) for model in queryset]

    def save(self, leave_type: LeaveType) -> LeaveType:
        """Save leave type."""
        model, created = LeaveTypeModel.objects.update_or_create(
            id=leave_type.id,
            defaults={
                "name": leave_type.name,
                "default_days_allowed": leave_type.default_days_allowed,
            },
        )
        return self._to_entity(model)

    def delete(self, leave_type_id: int) -> None:
        """Delete leave type."""
        LeaveTypeModel.objects.filter(id=leave_type_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = LeaveTypeModel.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, model: LeaveTypeModel) -> LeaveType:
        """Convert Django model to domain entity."""
        return LeaveType(
            id=model.id,
            name=model.name,
            default_days_allowed=model.default_days_allowed,
            is_active=True,  # Default to active since model doesn't have this field
        )

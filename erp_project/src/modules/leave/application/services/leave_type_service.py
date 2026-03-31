"""
Leave type application service.
"""

from dataclasses import dataclass
from typing import Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.leave.application.interfaces import ILeaveTypeRepository, LeaveTypeDTO
from modules.leave.domain.entities import LeaveType
from modules.leave.domain.events import LeaveTypeCreated


@dataclass
class CreateLeaveTypeCommand:
    """Command to create a leave type."""

    name: str
    default_days_allowed: int = 0
    is_active: bool = True


@dataclass
class UpdateLeaveTypeCommand:
    """Command to update a leave type."""

    leave_type_id: int
    name: str | None = None
    default_days_allowed: int | None = None
    is_active: bool | None = None


class LeaveTypeService:
    """
    Application service for leave type operations.

    Handles use cases related to leave types.
    """

    def __init__(self, leave_type_repository: ILeaveTypeRepository) -> None:
        self._repository = leave_type_repository

    def create_leave_type(self, command: CreateLeaveTypeCommand) -> LeaveTypeDTO:
        """Create a new leave type."""
        # Check for duplicate name
        existing = self._repository.get_by_name(command.name)
        if existing:
            raise ValidationError(f"Leave type with name '{command.name}' already exists")

        # Create leave type
        leave_type = LeaveType(
            id=self._repository.get_next_id(),
            name=command.name,
            default_days_allowed=command.default_days_allowed,
            is_active=command.is_active,
        )

        # Add domain event
        leave_type.add_domain_event(
            LeaveTypeCreated(
                leave_type_id=leave_type.id,
                name=leave_type.name,
                default_days_allowed=leave_type.default_days_allowed,
            )
        )

        # Save and return
        saved = self._repository.save(leave_type)
        return self._to_dto(saved)

    def update_leave_type(self, command: UpdateLeaveTypeCommand) -> LeaveTypeDTO:
        """Update an existing leave type."""
        leave_type = self._repository.get_by_id(command.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {command.leave_type_id} not found")

        # Update fields if provided
        if command.name is not None:
            # Check for duplicate name
            existing = self._repository.get_by_name(command.name)
            if existing and existing.id != leave_type.id:
                raise ValidationError(f"Leave type with name '{command.name}' already exists")
            leave_type.rename(command.name)

        if command.default_days_allowed is not None:
            leave_type.update_default_days(command.default_days_allowed)

        if command.is_active is not None:
            if command.is_active:
                leave_type.activate()
            else:
                leave_type.deactivate()

        # Save and return
        saved = self._repository.save(leave_type)
        return self._to_dto(saved)

    def get_leave_type(self, leave_type_id: int) -> LeaveTypeDTO:
        """Get a leave type by ID."""
        leave_type = self._repository.get_by_id(leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {leave_type_id} not found")
        return self._to_dto(leave_type)

    def get_all_leave_types(self, include_inactive: bool = False) -> Sequence[LeaveTypeDTO]:
        """Get all leave types."""
        leave_types = self._repository.get_all(include_inactive=include_inactive)
        return [self._to_dto(lt) for lt in leave_types]

    def delete_leave_type(self, leave_type_id: int) -> None:
        """Delete a leave type."""
        leave_type = self._repository.get_by_id(leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {leave_type_id} not found")
        self._repository.delete(leave_type_id)

    def _to_dto(self, leave_type: LeaveType) -> LeaveTypeDTO:
        """Convert entity to DTO."""
        return LeaveTypeDTO(
            id=leave_type.id,
            name=leave_type.name,
            default_days_allowed=leave_type.default_days_allowed,
            is_active=leave_type.is_active,
        )

"""
Organization application service for departments and positions.
"""

from dataclasses import dataclass

from shared.domain.exceptions import ValidationError, NotFoundError
from shared.infrastructure import EventBus

from modules.hr.application.interfaces import (
    IDepartmentRepository,
    IPositionRepository,
    IEmployeeRepository,
    DepartmentDTO,
    PositionDTO,
)
from modules.hr.domain.entities import Department, Position
from modules.hr.domain.events import (
    DepartmentCreatedEvent,
    DepartmentUpdatedEvent,
    DepartmentDeletedEvent,
    PositionCreatedEvent,
    PositionUpdatedEvent,
    PositionDeletedEvent,
)


@dataclass
class CreateDepartmentCommand:
    """Command to create a new department."""

    name: str
    description: str = ""


@dataclass
class UpdateDepartmentCommand:
    """Command to update a department."""

    department_id: int
    name: str | None = None
    description: str | None = None


@dataclass
class CreatePositionCommand:
    """Command to create a new position."""

    title: str
    department_id: int
    description: str = ""


@dataclass
class UpdatePositionCommand:
    """Command to update a position."""

    position_id: int
    title: str | None = None
    department_id: int | None = None
    description: str | None = None


class DepartmentService:
    """
    Application service for department operations.
    """

    def __init__(
        self,
        department_repository: IDepartmentRepository,
        employee_repository: IEmployeeRepository,
        event_bus: EventBus | None = None,
    ):
        """Initialize service with repositories."""
        self._departments = department_repository
        self._employees = employee_repository
        self._event_bus = event_bus or EventBus.get_instance()

    def create_department(self, command: CreateDepartmentCommand) -> Department:
        """
        Create a new department.

        Args:
            command: Create department command

        Returns:
            Created department
        """
        # Check uniqueness
        if self._departments.exists_by_name(command.name):
            raise ValidationError(
                message=f"Department with name '{command.name}' already exists",
                code="DUPLICATE_DEPARTMENT_NAME",
            )

        department = Department.create(
            id=0,  # Will be set by repository
            name=command.name,
            description=command.description,
        )

        self._departments.add(department)

        self._event_bus.publish(
            DepartmentCreatedEvent(
                department_id=department.id,
                name=department.name,
            )
        )

        return department

    def update_department(self, command: UpdateDepartmentCommand) -> Department:
        """
        Update an existing department.

        Args:
            command: Update department command

        Returns:
            Updated department
        """
        department = self._departments.get_by_id(command.department_id)
        if not department:
            raise NotFoundError(f"Department with ID {command.department_id} not found")

        changes = []

        if command.name and command.name != department.name:
            # Check uniqueness
            existing = self._departments.get_by_name(command.name)
            if existing and existing.id != department.id:
                raise ValidationError(
                    message=f"Department with name '{command.name}' already exists",
                    code="DUPLICATE_DEPARTMENT_NAME",
                )
            changes.append("name")

        if command.description is not None and command.description != department.description:
            changes.append("description")

        department.update(name=command.name, description=command.description)
        self._departments.update(department)

        if changes:
            self._event_bus.publish(
                DepartmentUpdatedEvent(
                    department_id=department.id,
                    name=department.name,
                    changes=tuple(changes),
                )
            )

        return department

    def delete_department(self, department_id: int) -> bool:
        """
        Delete a department.

        Args:
            department_id: Department ID

        Returns:
            True if deleted
        """
        department = self._departments.get_by_id(department_id)
        if not department:
            raise NotFoundError(f"Department with ID {department_id} not found")

        # Check if employees exist in department
        employees = self._employees.get_by_department(department_id)
        if employees:
            raise ValidationError(
                message=f"Cannot delete department with {len(employees)} employees",
                code="DEPARTMENT_HAS_EMPLOYEES",
            )

        deleted = self._departments.delete(department_id)

        if deleted:
            self._event_bus.publish(
                DepartmentDeletedEvent(
                    department_id=department_id,
                    name=department.name,
                )
            )

        return deleted

    def get_department(self, department_id: int) -> DepartmentDTO | None:
        """Get department DTO by ID."""
        department = self._departments.get_by_id(department_id)
        if not department:
            return None
        return self._to_dto(department)

    def get_all_departments(self) -> list[DepartmentDTO]:
        """Get all departments."""
        departments = self._departments.get_all()
        return [self._to_dto(d) for d in departments]

    def _to_dto(self, department: Department) -> DepartmentDTO:
        """Convert department entity to DTO."""
        employee_count = len(self._employees.get_by_department(department.id))
        return DepartmentDTO(
            id=department.id,
            name=department.name,
            description=department.description,
            employee_count=employee_count,
        )


class PositionService:
    """
    Application service for position operations.
    """

    def __init__(
        self,
        position_repository: IPositionRepository,
        department_repository: IDepartmentRepository,
        employee_repository: IEmployeeRepository,
        event_bus: EventBus | None = None,
    ):
        """Initialize service with repositories."""
        self._positions = position_repository
        self._departments = department_repository
        self._employees = employee_repository
        self._event_bus = event_bus or EventBus.get_instance()

    def create_position(self, command: CreatePositionCommand) -> Position:
        """
        Create a new position.

        Args:
            command: Create position command

        Returns:
            Created position
        """
        # Check department exists
        department = self._departments.get_by_id(command.department_id)
        if not department:
            raise NotFoundError(f"Department with ID {command.department_id} not found")

        # Check uniqueness
        if self._positions.exists_by_title(command.title):
            raise ValidationError(
                message=f"Position with title '{command.title}' already exists",
                code="DUPLICATE_POSITION_TITLE",
            )

        position = Position.create(
            id=0,  # Will be set by repository
            title=command.title,
            department_id=command.department_id,
            description=command.description,
        )

        self._positions.add(position)

        self._event_bus.publish(
            PositionCreatedEvent(
                position_id=position.id,
                title=position.title,
                department_id=position.department_id,
            )
        )

        return position

    def update_position(self, command: UpdatePositionCommand) -> Position:
        """
        Update an existing position.

        Args:
            command: Update position command

        Returns:
            Updated position
        """
        position = self._positions.get_by_id(command.position_id)
        if not position:
            raise NotFoundError(f"Position with ID {command.position_id} not found")

        changes = []

        if command.title and command.title != position.title:
            # Check uniqueness
            existing = self._positions.get_by_title(command.title)
            if existing and existing.id != position.id:
                raise ValidationError(
                    message=f"Position with title '{command.title}' already exists",
                    code="DUPLICATE_POSITION_TITLE",
                )
            changes.append("title")

        if command.department_id and command.department_id != position.department_id:
            # Check department exists
            department = self._departments.get_by_id(command.department_id)
            if not department:
                raise NotFoundError(f"Department with ID {command.department_id} not found")
            changes.append("department")

        if command.description is not None and command.description != position.description:
            changes.append("description")

        position.update(
            title=command.title,
            department_id=command.department_id,
            description=command.description,
        )
        self._positions.update(position)

        if changes:
            self._event_bus.publish(
                PositionUpdatedEvent(
                    position_id=position.id,
                    title=position.title,
                    changes=tuple(changes),
                )
            )

        return position

    def delete_position(self, position_id: int) -> bool:
        """
        Delete a position.

        Args:
            position_id: Position ID

        Returns:
            True if deleted
        """
        position = self._positions.get_by_id(position_id)
        if not position:
            raise NotFoundError(f"Position with ID {position_id} not found")

        # Check if employees have this position
        employees = self._employees.get_by_position(position_id)
        if employees:
            raise ValidationError(
                message=f"Cannot delete position with {len(employees)} employees",
                code="POSITION_HAS_EMPLOYEES",
            )

        deleted = self._positions.delete(position_id)

        if deleted:
            self._event_bus.publish(
                PositionDeletedEvent(
                    position_id=position_id,
                    title=position.title,
                )
            )

        return deleted

    def get_position(self, position_id: int) -> PositionDTO | None:
        """Get position DTO by ID."""
        position = self._positions.get_by_id(position_id)
        if not position:
            return None
        return self._to_dto(position)

    def get_positions_by_department(self, department_id: int) -> list[PositionDTO]:
        """Get positions in a department."""
        positions = self._positions.get_by_department(department_id)
        return [self._to_dto(p) for p in positions]

    def _to_dto(self, position: Position) -> PositionDTO:
        """Convert position entity to DTO."""
        dept_name = ""
        department = self._departments.get_by_id(position.department_id)
        if department:
            dept_name = department.name

        return PositionDTO(
            id=position.id,
            title=position.title,
            department_id=position.department_id,
            department_name=dept_name,
            description=position.description,
        )

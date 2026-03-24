"""
Domain events for organizational structure (departments, positions).
"""

from dataclasses import dataclass

from shared.domain.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class DepartmentCreatedEvent(DomainEvent):
    """Event raised when a new department is created."""

    department_id: int
    name: str


@dataclass(frozen=True, kw_only=True)
class DepartmentUpdatedEvent(DomainEvent):
    """Event raised when a department is updated."""

    department_id: int
    name: str
    changes: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class DepartmentDeletedEvent(DomainEvent):
    """Event raised when a department is deleted."""

    department_id: int
    name: str


@dataclass(frozen=True, kw_only=True)
class PositionCreatedEvent(DomainEvent):
    """Event raised when a new position is created."""

    position_id: int
    title: str
    department_id: int


@dataclass(frozen=True, kw_only=True)
class PositionUpdatedEvent(DomainEvent):
    """Event raised when a position is updated."""

    position_id: int
    title: str
    changes: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class PositionDeletedEvent(DomainEvent):
    """Event raised when a position is deleted."""

    position_id: int
    title: str


@dataclass(frozen=True, kw_only=True)
class PositionMovedEvent(DomainEvent):
    """Event raised when a position is moved to a different department."""

    position_id: int
    title: str
    old_department_id: int
    new_department_id: int

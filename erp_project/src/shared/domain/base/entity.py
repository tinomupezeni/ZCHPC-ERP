"""
Base class for Domain Entities.

Entities are objects that have a distinct identity that runs through time
and different states. They are compared by their ID, not by attributes.

Example:
    class Employee(Entity):
        def __init__(self, id: int, name: str):
            super().__init__(id)
            self.name = name
"""

from abc import ABC
from typing import Any, Generic, TypeVar

# Type variable for entity IDs (can be int, UUID, str, etc.)
TId = TypeVar("TId")


class Entity(ABC, Generic[TId]):
    """
    Base class for all entities in the domain.

    Entities are:
    - Identified by their ID (not by attributes)
    - Mutable (their state can change)
    - Equal only if they have the same ID

    Usage:
        class Employee(Entity[int]):
            def __init__(self, id: int, name: str, department: str):
                super().__init__(id)
                self.name = name
                self.department = department

            def transfer(self, new_department: str) -> None:
                self.department = new_department
    """

    def __init__(self, id: TId) -> None:
        """
        Initialize entity with its identity.

        Args:
            id: The unique identifier for this entity
        """
        self._id = id
        self._domain_events: list[Any] = []

    @property
    def id(self) -> TId:
        """The unique identifier for this entity."""
        return self._id

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on entity ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation showing class name and ID."""
        return f"{self.__class__.__name__}(id={self._id!r})"

    def add_domain_event(self, event: Any) -> None:
        """
        Add a domain event to be dispatched.

        Args:
            event: The domain event to add
        """
        self._domain_events.append(event)

    def clear_domain_events(self) -> list[Any]:
        """
        Clear and return all pending domain events.

        Returns:
            List of domain events that were pending
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    @property
    def domain_events(self) -> list[Any]:
        """List of pending domain events."""
        return self._domain_events.copy()

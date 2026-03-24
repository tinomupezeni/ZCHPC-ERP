"""
Base repository interfaces and abstract implementations.

Defines the contract that all repositories must follow,
providing consistent data access patterns across modules.

Example:
    class EmployeeRepository(BaseRepository[Employee, int]):
        def __init__(self, session):
            self.session = session

        def get(self, id: int) -> Employee | None:
            model = EmployeeModel.objects.filter(pk=id).first()
            return self._to_entity(model) if model else None
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.domain.base.aggregate import AggregateRoot
from shared.domain.base.entity import Entity

# Type variables for generic repository
TEntity = TypeVar("TEntity", bound=Entity[Any])
TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any])
TId = TypeVar("TId")


class IReadRepository(ABC, Generic[TEntity, TId]):
    """
    Read-only repository interface.

    Use for query-side operations where modifications are not needed.
    """

    @abstractmethod
    def get(self, id: TId) -> TEntity | None:
        """
        Get an entity by its ID.

        Args:
            id: The entity's unique identifier

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(self) -> list[TEntity]:
        """
        Get all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def exists(self, id: TId) -> bool:
        """
        Check if an entity with the given ID exists.

        Args:
            id: The entity's unique identifier

        Returns:
            True if entity exists, False otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count
        """
        pass


class IWriteRepository(ABC, Generic[TEntity, TId]):
    """
    Write repository interface.

    Use for command-side operations that modify state.
    """

    @abstractmethod
    def add(self, entity: TEntity) -> None:
        """
        Add a new entity.

        Args:
            entity: The entity to add
        """
        pass

    @abstractmethod
    def update(self, entity: TEntity) -> None:
        """
        Update an existing entity.

        Args:
            entity: The entity to update
        """
        pass

    @abstractmethod
    def delete(self, entity: TEntity) -> None:
        """
        Delete an entity.

        Args:
            entity: The entity to delete
        """
        pass

    @abstractmethod
    def delete_by_id(self, id: TId) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id: The entity's unique identifier

        Returns:
            True if entity was deleted, False if not found
        """
        pass


class IRepository(IReadRepository[TEntity, TId], IWriteRepository[TEntity, TId], ABC):
    """
    Full repository interface combining read and write operations.

    Most repositories will implement this interface.
    """

    pass


class IAggregateRepository(IRepository[TAggregate, TId], ABC, Generic[TAggregate, TId]):
    """
    Repository interface specifically for aggregate roots.

    Extends IRepository with aggregate-specific operations.
    """

    @abstractmethod
    def get_with_version(self, id: TId, expected_version: int) -> TAggregate | None:
        """
        Get an aggregate and verify its version for optimistic concurrency.

        Args:
            id: The aggregate's unique identifier
            expected_version: The expected version number

        Returns:
            The aggregate if found and version matches, None otherwise

        Raises:
            ConcurrencyError: If version doesn't match
        """
        pass


class BaseRepository(IRepository[TEntity, TId], ABC, Generic[TEntity, TId]):
    """
    Abstract base implementation for repositories.

    Provides common functionality that can be shared across
    different repository implementations.

    Subclasses must implement the abstract methods and can
    override the protected helper methods for entity mapping.
    """

    def exists(self, id: TId) -> bool:
        """Default implementation using get()."""
        return self.get(id) is not None

    def delete(self, entity: TEntity) -> None:
        """Default implementation using delete_by_id()."""
        self.delete_by_id(entity.id)


class InMemoryRepository(BaseRepository[TEntity, TId], Generic[TEntity, TId]):
    """
    In-memory repository implementation for testing.

    Stores entities in a dictionary. Useful for unit tests
    where database access is not needed.

    Usage:
        repo = InMemoryRepository[Employee, int]()
        repo.add(employee)
        found = repo.get(employee.id)
    """

    def __init__(self) -> None:
        """Initialize empty in-memory storage."""
        self._storage: dict[TId, TEntity] = {}

    def get(self, id: TId) -> TEntity | None:
        """Get entity from memory."""
        return self._storage.get(id)

    def get_all(self) -> list[TEntity]:
        """Get all entities from memory."""
        return list(self._storage.values())

    def count(self) -> int:
        """Count entities in memory."""
        return len(self._storage)

    def add(self, entity: TEntity) -> None:
        """Add entity to memory."""
        self._storage[entity.id] = entity

    def update(self, entity: TEntity) -> None:
        """Update entity in memory."""
        self._storage[entity.id] = entity

    def delete_by_id(self, id: TId) -> bool:
        """Delete entity from memory by ID."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    def clear(self) -> None:
        """Clear all entities from memory."""
        self._storage.clear()

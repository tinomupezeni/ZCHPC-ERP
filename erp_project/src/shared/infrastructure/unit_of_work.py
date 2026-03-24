"""
Unit of Work pattern for transaction management.

Coordinates changes across multiple repositories within a single
transaction, ensuring atomicity and consistency.

Example:
    async with unit_of_work:
        employee = await unit_of_work.employees.get(employee_id)
        employee.update_salary(new_salary)
        await unit_of_work.commit()
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypeVar

from shared.domain.base.aggregate import AggregateRoot
from shared.domain.base.domain_event import DomainEvent
from shared.infrastructure.event_bus import EventBus, get_event_bus

TAggregate = TypeVar("TAggregate", bound=AggregateRoot[Any])


class IRepository(Protocol[TAggregate]):
    """
    Base repository protocol defining standard operations.

    All repositories should implement these methods.
    """

    async def get(self, id: Any) -> TAggregate | None:
        """Get an aggregate by ID."""
        ...

    async def add(self, aggregate: TAggregate) -> None:
        """Add a new aggregate."""
        ...

    async def update(self, aggregate: TAggregate) -> None:
        """Update an existing aggregate."""
        ...

    async def delete(self, aggregate: TAggregate) -> None:
        """Delete an aggregate."""
        ...


class IUnitOfWork(ABC):
    """
    Abstract Unit of Work interface.

    Implementations provide access to repositories and manage transactions.
    Domain events are collected from aggregates and published on commit.

    Usage:
        class SqlUnitOfWork(IUnitOfWork):
            def __init__(self, session_factory):
                self.session_factory = session_factory

            async def __aenter__(self):
                self.session = self.session_factory()
                self.employees = EmployeeRepository(self.session)
                return self

            async def commit(self):
                await self._publish_domain_events()
                await self.session.commit()

            async def rollback(self):
                await self.session.rollback()
    """

    def __init__(self) -> None:
        """Initialize unit of work."""
        self._new_aggregates: list[AggregateRoot[Any]] = []
        self._dirty_aggregates: list[AggregateRoot[Any]] = []
        self._event_bus: EventBus = get_event_bus()

    async def __aenter__(self) -> "IUnitOfWork":
        """Enter the unit of work context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the unit of work context."""
        if exc_type is not None:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit all changes in this unit of work.

        Should:
        1. Persist all new and modified aggregates
        2. Collect and publish domain events
        3. Commit the database transaction
        """
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback all changes in this unit of work.

        Should:
        1. Discard all pending changes
        2. Clear collected domain events
        3. Rollback the database transaction
        """
        pass

    def register_new(self, aggregate: AggregateRoot[Any]) -> None:
        """
        Register a new aggregate to be inserted.

        Args:
            aggregate: The aggregate to insert
        """
        if aggregate not in self._new_aggregates:
            self._new_aggregates.append(aggregate)

    def register_dirty(self, aggregate: AggregateRoot[Any]) -> None:
        """
        Register an aggregate that has been modified.

        Args:
            aggregate: The modified aggregate
        """
        if aggregate not in self._dirty_aggregates and aggregate not in self._new_aggregates:
            self._dirty_aggregates.append(aggregate)

    def _collect_domain_events(self) -> list[DomainEvent]:
        """
        Collect all domain events from registered aggregates.

        Returns:
            List of domain events to publish
        """
        events: list[DomainEvent] = []

        for aggregate in self._new_aggregates + self._dirty_aggregates:
            events.extend(aggregate.clear_domain_events())

        return events

    async def _publish_domain_events(self) -> None:
        """Publish all collected domain events."""
        events = self._collect_domain_events()
        for event in events:
            self._event_bus.publish(event)

    def _clear_tracking(self) -> None:
        """Clear all tracked aggregates."""
        self._new_aggregates.clear()
        self._dirty_aggregates.clear()


class DjangoUnitOfWork(IUnitOfWork):
    """
    Django-specific Unit of Work implementation.

    Uses Django's transaction management for atomicity.
    Repositories are attached as properties.

    Usage:
        async with DjangoUnitOfWork() as uow:
            employee = await uow.employees.get(1)
            employee.update_salary(new_salary)
            uow.register_dirty(employee)
            await uow.commit()
    """

    def __init__(self) -> None:
        """Initialize Django unit of work."""
        super().__init__()
        self._committed = False

    async def __aenter__(self) -> "DjangoUnitOfWork":
        """Enter transaction context."""
        # Django handles transaction automatically with ATOMIC_REQUESTS
        # or we can use transaction.atomic() for explicit control
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit transaction context."""
        if exc_type is not None:
            await self.rollback()
        elif not self._committed:
            # Auto-rollback if not explicitly committed
            await self.rollback()

    async def commit(self) -> None:
        """
        Commit the unit of work.

        Publishes domain events and marks as committed.
        Actual database commit is handled by Django's transaction management.
        """
        await self._publish_domain_events()
        self._committed = True
        self._clear_tracking()

    async def rollback(self) -> None:
        """
        Rollback the unit of work.

        Clears tracked aggregates without publishing events.
        Actual rollback is handled by Django's transaction management.
        """
        self._clear_tracking()
        self._committed = False


class SyncUnitOfWork:
    """
    Synchronous Unit of Work for non-async contexts.

    Provides the same functionality as IUnitOfWork but with
    synchronous methods for use in Django views without async.
    """

    def __init__(self) -> None:
        """Initialize synchronous unit of work."""
        self._new_aggregates: list[AggregateRoot[Any]] = []
        self._dirty_aggregates: list[AggregateRoot[Any]] = []
        self._event_bus: EventBus = get_event_bus()
        self._committed = False

    def __enter__(self) -> "SyncUnitOfWork":
        """Enter the unit of work context."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the unit of work context."""
        if exc_type is not None:
            self.rollback()
        elif not self._committed:
            self.rollback()

    def commit(self) -> None:
        """Commit all changes and publish domain events."""
        self._publish_domain_events()
        self._committed = True
        self._clear_tracking()

    def rollback(self) -> None:
        """Rollback all changes."""
        self._clear_tracking()
        self._committed = False

    def register_new(self, aggregate: AggregateRoot[Any]) -> None:
        """Register a new aggregate to be inserted."""
        if aggregate not in self._new_aggregates:
            self._new_aggregates.append(aggregate)

    def register_dirty(self, aggregate: AggregateRoot[Any]) -> None:
        """Register an aggregate that has been modified."""
        if aggregate not in self._dirty_aggregates and aggregate not in self._new_aggregates:
            self._dirty_aggregates.append(aggregate)

    def _collect_domain_events(self) -> list[DomainEvent]:
        """Collect all domain events from registered aggregates."""
        events: list[DomainEvent] = []
        for aggregate in self._new_aggregates + self._dirty_aggregates:
            events.extend(aggregate.clear_domain_events())
        return events

    def _publish_domain_events(self) -> None:
        """Publish all collected domain events."""
        events = self._collect_domain_events()
        for event in events:
            self._event_bus.publish(event)

    def _clear_tracking(self) -> None:
        """Clear all tracked aggregates."""
        self._new_aggregates.clear()
        self._dirty_aggregates.clear()

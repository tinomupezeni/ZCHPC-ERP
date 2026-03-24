"""
Tests for shared infrastructure: EventBus, UnitOfWork, Repository.
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from shared.domain.base import AggregateRoot
from shared.domain.base.domain_event import DomainEvent
from shared.infrastructure import InMemoryRepository
from shared.infrastructure.event_bus import EventBus, get_event_bus
from shared.infrastructure.unit_of_work import SyncUnitOfWork


# =============================================================================
# Test Domain Events
# =============================================================================


@dataclass(frozen=True)
class TestEvent(DomainEvent):
    """Test event for testing."""

    message: str


@dataclass(frozen=True)
class AnotherEvent(DomainEvent):
    """Another test event."""

    value: int


class TestDomainEvent:
    """Tests for DomainEvent base class."""

    def test_event_has_id_and_timestamp(self):
        event = TestEvent(message="test")
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_event_type_property(self):
        event = TestEvent(message="test")
        assert event.event_type == "TestEvent"

    def test_event_to_dict(self):
        event = TestEvent(message="hello")
        data = event.to_dict()
        assert data["event_type"] == "TestEvent"
        assert data["message"] == "hello"
        assert "event_id" in data
        assert "occurred_at" in data

    def test_event_is_immutable(self):
        event = TestEvent(message="test")
        with pytest.raises(AttributeError):
            event.message = "changed"  # type: ignore


# =============================================================================
# Test EventBus
# =============================================================================


class TestEventBus:
    """Tests for EventBus."""

    def setup_method(self):
        """Reset singleton before each test."""
        EventBus.reset_instance()

    def test_subscribe_and_publish(self):
        bus = EventBus()
        received: list[TestEvent] = []

        def handler(event: TestEvent):
            received.append(event)

        bus.subscribe(TestEvent, handler)
        event = TestEvent(message="hello")
        bus.publish(event)

        assert len(received) == 1
        assert received[0].message == "hello"

    def test_multiple_handlers(self):
        bus = EventBus()
        results: list[str] = []

        def handler1(event: TestEvent):
            results.append("handler1")

        def handler2(event: TestEvent):
            results.append("handler2")

        bus.subscribe(TestEvent, handler1)
        bus.subscribe(TestEvent, handler2)
        bus.publish(TestEvent(message="test"))

        assert len(results) == 2
        assert "handler1" in results
        assert "handler2" in results

    def test_handler_decorator(self):
        bus = EventBus()
        received: list[TestEvent] = []

        @bus.handler(TestEvent)
        def my_handler(event: TestEvent):
            received.append(event)

        bus.publish(TestEvent(message="decorated"))
        assert len(received) == 1

    def test_unsubscribe(self):
        bus = EventBus()
        received: list[TestEvent] = []

        def handler(event: TestEvent):
            received.append(event)

        bus.subscribe(TestEvent, handler)
        bus.unsubscribe(TestEvent, handler)
        bus.publish(TestEvent(message="test"))

        assert len(received) == 0

    def test_different_event_types(self):
        bus = EventBus()
        test_events: list[TestEvent] = []
        another_events: list[AnotherEvent] = []

        bus.subscribe(TestEvent, lambda e: test_events.append(e))
        bus.subscribe(AnotherEvent, lambda e: another_events.append(e))

        bus.publish(TestEvent(message="hello"))
        bus.publish(AnotherEvent(value=42))

        assert len(test_events) == 1
        assert len(another_events) == 1
        assert another_events[0].value == 42

    def test_publish_all(self):
        bus = EventBus()
        received: list[DomainEvent] = []

        bus.subscribe(TestEvent, lambda e: received.append(e))
        bus.subscribe(AnotherEvent, lambda e: received.append(e))

        events = [TestEvent(message="1"), AnotherEvent(value=2), TestEvent(message="3")]
        bus.publish_all(events)

        assert len(received) == 3

    def test_handler_error_in_non_strict_mode(self):
        bus = EventBus(strict_mode=False)

        def bad_handler(event: TestEvent):
            raise ValueError("Handler error")

        def good_handler(event: TestEvent):
            pass  # This should still run

        bus.subscribe(TestEvent, bad_handler)
        bus.subscribe(TestEvent, good_handler)

        # Should not raise, error is logged
        bus.publish(TestEvent(message="test"))

    def test_handler_error_in_strict_mode(self):
        bus = EventBus(strict_mode=True)

        def bad_handler(event: TestEvent):
            raise ValueError("Handler error")

        bus.subscribe(TestEvent, bad_handler)

        with pytest.raises(ValueError):
            bus.publish(TestEvent(message="test"))

    def test_clear_handlers(self):
        bus = EventBus()
        bus.subscribe(TestEvent, lambda e: None)
        bus.subscribe(AnotherEvent, lambda e: None)

        bus.clear_handlers(TestEvent)
        assert len(bus.get_handlers(TestEvent)) == 0
        assert len(bus.get_handlers(AnotherEvent)) == 1

        bus.clear_handlers()  # Clear all
        assert len(bus.get_handlers(AnotherEvent)) == 0

    def test_published_events_tracking(self):
        bus = EventBus()
        event1 = TestEvent(message="1")
        event2 = TestEvent(message="2")

        bus.publish(event1)
        bus.publish(event2)

        assert len(bus.published_events) == 2
        assert event1 in bus.published_events
        assert event2 in bus.published_events

        bus.clear_published_events()
        assert len(bus.published_events) == 0

    def test_singleton_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2


# =============================================================================
# Test SyncUnitOfWork
# =============================================================================


class TestAggregate(AggregateRoot[int]):
    """Test aggregate for testing."""

    def __init__(self, id: int, name: str):
        super().__init__(id)
        self.name = name


class TestSyncUnitOfWork:
    """Tests for SyncUnitOfWork."""

    def setup_method(self):
        """Reset event bus singleton before each test."""
        EventBus.reset_instance()

    def test_register_new_aggregate(self):
        uow = SyncUnitOfWork()
        aggregate = TestAggregate(id=1, name="Test")

        uow.register_new(aggregate)
        # Internal state check
        assert aggregate in uow._new_aggregates

    def test_register_dirty_aggregate(self):
        uow = SyncUnitOfWork()
        aggregate = TestAggregate(id=1, name="Test")

        uow.register_dirty(aggregate)
        assert aggregate in uow._dirty_aggregates

    def test_commit_publishes_domain_events(self):
        uow = SyncUnitOfWork()
        aggregate = TestAggregate(id=1, name="Test")
        event = TestEvent(message="created")
        aggregate.add_domain_event(event)

        uow.register_new(aggregate)

        received: list[TestEvent] = []
        uow._event_bus.subscribe(TestEvent, lambda e: received.append(e))

        uow.commit()

        assert len(received) == 1
        assert received[0].message == "created"

    def test_commit_clears_tracking(self):
        uow = SyncUnitOfWork()
        aggregate = TestAggregate(id=1, name="Test")

        uow.register_new(aggregate)
        uow.commit()

        assert len(uow._new_aggregates) == 0

    def test_rollback_clears_tracking(self):
        uow = SyncUnitOfWork()
        aggregate = TestAggregate(id=1, name="Test")
        aggregate.add_domain_event(TestEvent(message="test"))

        uow.register_new(aggregate)
        uow.rollback()

        assert len(uow._new_aggregates) == 0
        # Events should NOT be published on rollback

    def test_context_manager_commits_on_success(self):
        received: list[TestEvent] = []

        with SyncUnitOfWork() as uow:
            uow._event_bus.subscribe(TestEvent, lambda e: received.append(e))
            aggregate = TestAggregate(id=1, name="Test")
            aggregate.add_domain_event(TestEvent(message="test"))
            uow.register_new(aggregate)
            uow.commit()

        assert len(received) == 1

    def test_context_manager_rollback_on_exception(self):
        uow = SyncUnitOfWork()

        try:
            with uow:
                aggregate = TestAggregate(id=1, name="Test")
                uow.register_new(aggregate)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Should have rolled back
        assert len(uow._new_aggregates) == 0


# =============================================================================
# Test InMemoryRepository
# =============================================================================


class TestInMemoryRepository:
    """Tests for InMemoryRepository."""

    def test_add_and_get(self):
        repo = InMemoryRepository[TestAggregate, int]()
        aggregate = TestAggregate(id=1, name="Test")

        repo.add(aggregate)
        found = repo.get(1)

        assert found is not None
        assert found.name == "Test"

    def test_get_nonexistent_returns_none(self):
        repo = InMemoryRepository[TestAggregate, int]()
        found = repo.get(999)
        assert found is None

    def test_get_all(self):
        repo = InMemoryRepository[TestAggregate, int]()
        repo.add(TestAggregate(id=1, name="One"))
        repo.add(TestAggregate(id=2, name="Two"))

        all_items = repo.get_all()
        assert len(all_items) == 2

    def test_count(self):
        repo = InMemoryRepository[TestAggregate, int]()
        assert repo.count() == 0

        repo.add(TestAggregate(id=1, name="One"))
        assert repo.count() == 1

    def test_exists(self):
        repo = InMemoryRepository[TestAggregate, int]()
        repo.add(TestAggregate(id=1, name="Test"))

        assert repo.exists(1)
        assert not repo.exists(999)

    def test_update(self):
        repo = InMemoryRepository[TestAggregate, int]()
        aggregate = TestAggregate(id=1, name="Original")
        repo.add(aggregate)

        aggregate.name = "Updated"
        repo.update(aggregate)

        found = repo.get(1)
        assert found is not None
        assert found.name == "Updated"

    def test_delete(self):
        repo = InMemoryRepository[TestAggregate, int]()
        aggregate = TestAggregate(id=1, name="Test")
        repo.add(aggregate)

        repo.delete(aggregate)
        assert repo.get(1) is None

    def test_delete_by_id(self):
        repo = InMemoryRepository[TestAggregate, int]()
        repo.add(TestAggregate(id=1, name="Test"))

        result = repo.delete_by_id(1)
        assert result is True
        assert repo.get(1) is None

    def test_delete_by_id_nonexistent(self):
        repo = InMemoryRepository[TestAggregate, int]()
        result = repo.delete_by_id(999)
        assert result is False

    def test_clear(self):
        repo = InMemoryRepository[TestAggregate, int]()
        repo.add(TestAggregate(id=1, name="One"))
        repo.add(TestAggregate(id=2, name="Two"))

        repo.clear()
        assert repo.count() == 0

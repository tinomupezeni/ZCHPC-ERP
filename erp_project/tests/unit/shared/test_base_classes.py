"""
Tests for base domain classes: Entity, AggregateRoot, ValueObject.
"""

from dataclasses import dataclass

import pytest

from shared.domain.base import AggregateRoot, Entity, ValueObject
from shared.domain.base.domain_event import DomainEvent


# =============================================================================
# Test Value Objects
# =============================================================================


@dataclass(frozen=True)
class TestAddress(ValueObject):
    """Test value object for testing."""

    street: str
    city: str
    zip_code: str


class TestValueObject:
    """Tests for ValueObject base class."""

    def test_value_objects_with_same_values_are_equal(self):
        addr1 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        addr2 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        assert addr1 == addr2

    def test_value_objects_with_different_values_are_not_equal(self):
        addr1 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        addr2 = TestAddress(street="456 Oak", city="Harare", zip_code="00263")
        assert addr1 != addr2

    def test_value_object_is_hashable(self):
        addr = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        # Should not raise
        hash_value = hash(addr)
        assert isinstance(hash_value, int)

    def test_same_value_objects_have_same_hash(self):
        addr1 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        addr2 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        assert hash(addr1) == hash(addr2)

    def test_value_object_is_immutable(self):
        addr = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        with pytest.raises(AttributeError):
            addr.street = "456 Oak"  # type: ignore

    def test_value_object_can_be_used_in_set(self):
        addr1 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        addr2 = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        addr3 = TestAddress(street="456 Oak", city="Harare", zip_code="00263")

        addresses = {addr1, addr2, addr3}
        assert len(addresses) == 2  # addr1 and addr2 are the same

    def test_value_object_repr(self):
        addr = TestAddress(street="123 Main", city="Harare", zip_code="00263")
        repr_str = repr(addr)
        assert "TestAddress" in repr_str
        assert "123 Main" in repr_str


# =============================================================================
# Test Entities
# =============================================================================


class TestEmployee(Entity[int]):
    """Test entity for testing."""

    def __init__(self, id: int, name: str):
        super().__init__(id)
        self.name = name


class TestEntity:
    """Tests for Entity base class."""

    def test_entities_with_same_id_are_equal(self):
        emp1 = TestEmployee(id=1, name="John")
        emp2 = TestEmployee(id=1, name="Jane")  # Different name, same ID
        assert emp1 == emp2

    def test_entities_with_different_id_are_not_equal(self):
        emp1 = TestEmployee(id=1, name="John")
        emp2 = TestEmployee(id=2, name="John")  # Same name, different ID
        assert emp1 != emp2

    def test_entity_is_hashable_by_id(self):
        emp = TestEmployee(id=1, name="John")
        assert hash(emp) == hash(1)

    def test_entity_can_be_used_in_set(self):
        emp1 = TestEmployee(id=1, name="John")
        emp2 = TestEmployee(id=1, name="Jane")  # Same ID
        emp3 = TestEmployee(id=2, name="John")

        employees = {emp1, emp2, emp3}
        assert len(employees) == 2  # emp1 and emp2 have same ID

    def test_entity_id_property(self):
        emp = TestEmployee(id=42, name="John")
        assert emp.id == 42

    def test_entity_is_mutable(self):
        emp = TestEmployee(id=1, name="John")
        emp.name = "Jane"
        assert emp.name == "Jane"

    def test_entity_repr(self):
        emp = TestEmployee(id=1, name="John")
        repr_str = repr(emp)
        assert "TestEmployee" in repr_str
        assert "1" in repr_str


# =============================================================================
# Test Domain Events on Entities
# =============================================================================


@dataclass(frozen=True)
class NameChangedEvent(DomainEvent):
    """Test event for entity domain events."""

    entity_id: int
    old_name: str
    new_name: str


class TestEntityDomainEvents:
    """Tests for domain event handling on entities."""

    def test_entity_can_add_domain_event(self):
        emp = TestEmployee(id=1, name="John")
        event = NameChangedEvent(entity_id=1, old_name="John", new_name="Jane")
        emp.add_domain_event(event)
        assert len(emp.domain_events) == 1
        assert emp.domain_events[0] == event

    def test_entity_domain_events_property_returns_copy(self):
        emp = TestEmployee(id=1, name="John")
        event = NameChangedEvent(entity_id=1, old_name="John", new_name="Jane")
        emp.add_domain_event(event)

        events = emp.domain_events
        events.clear()  # Modifying the copy

        assert len(emp.domain_events) == 1  # Original unchanged

    def test_clear_domain_events_returns_events_and_clears(self):
        emp = TestEmployee(id=1, name="John")
        event = NameChangedEvent(entity_id=1, old_name="John", new_name="Jane")
        emp.add_domain_event(event)

        cleared = emp.clear_domain_events()

        assert len(cleared) == 1
        assert cleared[0] == event
        assert len(emp.domain_events) == 0


# =============================================================================
# Test Aggregate Roots
# =============================================================================


class TestOrder(AggregateRoot[int]):
    """Test aggregate for testing."""

    def __init__(self, id: int, customer: str):
        super().__init__(id)
        self.customer = customer
        self._items: list[str] = []

    def add_item(self, item: str) -> None:
        self._items.append(item)


class TestAggregateRoot:
    """Tests for AggregateRoot base class."""

    def test_aggregate_inherits_entity_equality(self):
        order1 = TestOrder(id=1, customer="John")
        order2 = TestOrder(id=1, customer="Jane")
        assert order1 == order2  # Same ID

    def test_aggregate_has_version(self):
        order = TestOrder(id=1, customer="John")
        assert order.version == 0

    def test_aggregate_version_can_be_incremented(self):
        order = TestOrder(id=1, customer="John")
        order.increment_version()
        assert order.version == 1
        order.increment_version()
        assert order.version == 2

    def test_aggregate_inherits_domain_events(self):
        order = TestOrder(id=1, customer="John")
        event = NameChangedEvent(entity_id=1, old_name="", new_name="")
        order.add_domain_event(event)
        assert len(order.domain_events) == 1

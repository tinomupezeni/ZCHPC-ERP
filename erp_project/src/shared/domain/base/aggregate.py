"""
Base class for Aggregate Roots.

An Aggregate Root is an entity that serves as the entry point to an aggregate.
All external access to the aggregate must go through the root.
The root ensures consistency of the entire aggregate.

Example:
    class Order(AggregateRoot):
        def __init__(self, id: int, customer_id: int):
            super().__init__(id)
            self.customer_id = customer_id
            self._items: list[OrderItem] = []

        def add_item(self, product_id: int, quantity: int) -> None:
            # Business rules enforced here
            self._items.append(OrderItem(product_id, quantity))
"""

from typing import TypeVar

from shared.domain.base.entity import Entity

TId = TypeVar("TId")


class AggregateRoot(Entity[TId]):
    """
    Base class for all aggregate roots in the domain.

    Aggregate roots are:
    - The single entry point to an aggregate
    - Responsible for maintaining consistency
    - The only objects that repositories work with
    - Publishers of domain events

    Usage:
        class Employee(AggregateRoot[int]):
            def __init__(self, id: int, name: str):
                super().__init__(id)
                self.name = name
                self._contracts: list[Contract] = []

            def add_contract(self, contract: Contract) -> None:
                # Validate business rules
                if self.has_active_contract():
                    raise BusinessRuleViolation("Employee already has active contract")
                self._contracts.append(contract)
                self.add_domain_event(ContractAddedEvent(self.id, contract.id))

            def has_active_contract(self) -> bool:
                return any(c.is_active for c in self._contracts)

    Rules:
        1. Only aggregate roots are returned from repositories
        2. References to entities inside an aggregate are transient
        3. Only the root can be directly accessed
        4. Consistency boundaries are defined by the aggregate
    """

    def __init__(self, id: TId) -> None:
        """
        Initialize aggregate root.

        Args:
            id: The unique identifier for this aggregate
        """
        super().__init__(id)
        self._version: int = 0

    @property
    def version(self) -> int:
        """
        Version number for optimistic concurrency control.

        Incremented each time the aggregate is persisted.
        Used to detect concurrent modifications.
        """
        return self._version

    def increment_version(self) -> None:
        """Increment the version number after persistence."""
        self._version += 1

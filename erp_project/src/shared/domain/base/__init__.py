"""
Base classes for domain modeling.

These classes form the foundation of the domain layer:
- ValueObject: Immutable objects compared by value
- Entity: Objects with identity
- AggregateRoot: Entry points to aggregates
- DomainEvent: Events that occur in the domain
"""

from shared.domain.base.aggregate import AggregateRoot
from shared.domain.base.domain_event import DomainEvent
from shared.domain.base.entity import Entity
from shared.domain.base.value_object import ValueObject

__all__ = [
    "ValueObject",
    "Entity",
    "AggregateRoot",
    "DomainEvent",
]

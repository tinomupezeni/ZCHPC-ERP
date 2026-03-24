"""
Shared domain components.

Provides the building blocks for domain modeling:
- Base classes for entities, aggregates, and value objects
- Domain event base class
- Domain exceptions
- Common value objects (Money, DateRange, Period, etc.)
"""

from shared.domain.base import AggregateRoot, Entity, ValueObject
from shared.domain.base.domain_event import DomainEvent
from shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConcurrencyError,
    ConflictError,
    DomainException,
    InvalidOperationError,
    NotFoundError,
    ValidationError,
)
from shared.domain.value_objects import (
    Currency,
    DateRange,
    Email,
    EmployeeId,
    Money,
    NationalId,
    Period,
    PhoneNumber,
)

__all__ = [
    # Base classes
    "Entity",
    "AggregateRoot",
    "ValueObject",
    "DomainEvent",
    # Exceptions
    "DomainException",
    "ValidationError",
    "BusinessRuleViolationError",
    "NotFoundError",
    "ConflictError",
    "AuthorizationError",
    "ConcurrencyError",
    "InvalidOperationError",
    # Value objects
    "Money",
    "Currency",
    "DateRange",
    "Period",
    "Email",
    "PhoneNumber",
    "NationalId",
    "EmployeeId",
]

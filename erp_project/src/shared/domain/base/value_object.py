"""
Base class for Value Objects.

Value objects are immutable objects that are defined by their attributes
rather than by identity. Two value objects with the same attributes are equal.

Example:
    class Money(ValueObject):
        amount: Decimal
        currency: str
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueObject(ABC):
    """
    Base class for all value objects in the domain.

    Value objects are:
    - Immutable (frozen=True ensures this)
    - Compared by value (all attributes must match)
    - Have no identity

    Usage:
        @dataclass(frozen=True)
        class Money(ValueObject):
            amount: Decimal
            currency: str

            def add(self, other: 'Money') -> 'Money':
                if self.currency != other.currency:
                    raise ValueError("Cannot add different currencies")
                return Money(amount=self.amount + other.amount, currency=self.currency)
    """

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if all their attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Value objects can be hashed based on their attributes."""
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        """String representation showing class name and attributes."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"

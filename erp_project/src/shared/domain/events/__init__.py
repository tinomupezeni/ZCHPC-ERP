"""
Shared domain events module.

Re-exports DomainEvent from the base module for convenience.
"""

from shared.domain.base.domain_event import DomainEvent

__all__ = ["DomainEvent"]

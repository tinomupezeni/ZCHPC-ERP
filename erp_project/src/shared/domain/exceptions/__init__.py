"""
Domain exceptions for business rule violations.

All exceptions inherit from DomainException and can be caught
by the API layer for consistent error handling.
"""

from shared.domain.exceptions.domain_exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConcurrencyError,
    ConflictError,
    DomainException,
    InvalidOperationError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "DomainException",
    "ValidationError",
    "BusinessRuleViolationError",
    "NotFoundError",
    "ConflictError",
    "AuthorizationError",
    "ConcurrencyError",
    "InvalidOperationError",
]

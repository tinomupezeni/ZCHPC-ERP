"""
Domain exceptions for business rule violations.

These exceptions represent domain-level errors that should be caught
and translated to appropriate HTTP responses by the API layer.

Usage:
    if not employee.is_active:
        raise BusinessRuleViolationError(
            "Cannot process payroll for inactive employee",
            code="INACTIVE_EMPLOYEE"
        )
"""

from typing import Any


class DomainException(Exception):
    """
    Base exception for all domain-level errors.

    All domain exceptions should inherit from this class.
    This allows the API layer to catch all domain exceptions
    and translate them appropriately.
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize domain exception.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "INVALID_AMOUNT")
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(DomainException):
    """
    Raised when input data fails validation.

    Use for invalid data that doesn't meet domain requirements.

    Example:
        if amount < 0:
            raise ValidationError(
                "Amount cannot be negative",
                code="NEGATIVE_AMOUNT",
                details={"amount": amount}
            )
    """

    pass


class BusinessRuleViolationError(DomainException):
    """
    Raised when a business rule is violated.

    Use when an operation violates domain invariants or business logic.

    Example:
        if employee.leave_balance < requested_days:
            raise BusinessRuleViolationError(
                "Insufficient leave balance",
                code="INSUFFICIENT_LEAVE_BALANCE",
                details={
                    "available": employee.leave_balance,
                    "requested": requested_days
                }
            )
    """

    pass


class NotFoundError(DomainException):
    """
    Raised when a requested entity is not found.

    Use when an aggregate or entity cannot be located.

    Example:
        employee = repository.get(employee_id)
        if employee is None:
            raise NotFoundError(
                f"Employee with ID {employee_id} not found",
                code="EMPLOYEE_NOT_FOUND",
                details={"employee_id": employee_id}
            )
    """

    pass


class ConflictError(DomainException):
    """
    Raised when an operation conflicts with existing data.

    Use for duplicate entries, concurrent modification conflicts, etc.

    Example:
        if repository.exists_by_email(email):
            raise ConflictError(
                f"User with email {email} already exists",
                code="DUPLICATE_EMAIL",
                details={"email": email}
            )
    """

    pass


class AuthorizationError(DomainException):
    """
    Raised when a user is not authorized to perform an action.

    Use when permission checks fail at the domain level.

    Example:
        if not user.can_approve_leave():
            raise AuthorizationError(
                "User is not authorized to approve leave requests",
                code="UNAUTHORIZED_LEAVE_APPROVAL"
            )
    """

    pass


class ConcurrencyError(DomainException):
    """
    Raised when optimistic concurrency check fails.

    Use when the aggregate version doesn't match expected version.

    Example:
        if aggregate.version != expected_version:
            raise ConcurrencyError(
                "The record was modified by another user",
                code="CONCURRENT_MODIFICATION",
                details={
                    "expected_version": expected_version,
                    "actual_version": aggregate.version
                }
            )
    """

    pass


class InvalidOperationError(DomainException):
    """
    Raised when an operation is invalid for the current state.

    Use when an entity is in a state that doesn't allow the operation.

    Example:
        if payroll.status == PayrollStatus.CLOSED:
            raise InvalidOperationError(
                "Cannot modify a closed payroll",
                code="PAYROLL_CLOSED",
                details={"payroll_id": payroll.id, "status": payroll.status}
            )
    """

    pass

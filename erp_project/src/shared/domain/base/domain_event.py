"""
Base class for Domain Events.

Domain events represent something that happened in the domain that other
parts of the system might be interested in. They are immutable and
capture the state at the time the event occurred.

Example:
    @dataclass(frozen=True)
    class EmployeeHiredEvent(DomainEvent):
        employee_id: int
        department_id: int
        hired_date: date
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Base class for all domain events.

    Domain events are:
    - Immutable (frozen=True)
    - Named in past tense (something that happened)
    - Self-contained (carry all data needed)
    - Timestamped (when the event occurred)

    Usage:
        @dataclass(frozen=True)
        class PayrollProcessedEvent(DomainEvent):
            payroll_id: int
            period_year: int
            period_month: int
            total_employees: int
            total_net_pay: Decimal

    Naming conventions:
        - Use past tense: EmployeeHired, PayrollProcessed, LeaveApproved
        - Be specific: OrderShipped (not OrderUpdated)
        - Include aggregate ID: employee_id, order_id

    Event handlers should:
        - Be idempotent (safe to process multiple times)
        - Not modify the event
        - Handle failures gracefully
    """

    # Unique identifier for this event instance
    event_id: UUID = field(default_factory=uuid4)

    # When the event occurred
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """
        The type name of this event.

        Used for serialization and routing.
        Returns the class name (e.g., 'EmployeeHiredEvent').
        """
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Returns:
            Dictionary with all event data
        """
        result: dict[str, Any] = {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
        }

        # Add all other fields from the dataclass
        for key, value in self.__dict__.items():
            if key not in ("event_id", "occurred_at"):
                # Handle special types
                if isinstance(value, UUID):
                    result[key] = str(value)
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif hasattr(value, "to_dict"):
                    result[key] = value.to_dict()
                else:
                    result[key] = value

        return result

    def __repr__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}(event_id={self.event_id}, occurred_at={self.occurred_at})"

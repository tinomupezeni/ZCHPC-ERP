"""
SupportTicket aggregate root and TicketMessage entity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from shared.domain.base import AggregateRoot, Entity
from modules.portal.domain.value_objects import (
    TicketStatus,
    TicketCategory,
    TicketPriority,
    TicketNumber,
)


@dataclass
class TicketMessage(Entity[int]):
    """A message or reply on a support ticket."""

    ticket_id: Optional[int]
    sender_id: int
    message: str
    attachment_path: Optional[str] = None
    is_internal: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        sender_id: int,
        message: str,
        attachment_path: Optional[str] = None,
        is_internal: bool = False,
    ) -> "TicketMessage":
        """Create a new ticket message."""
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        return cls(
            id=None,
            ticket_id=None,
            sender_id=sender_id,
            message=message.strip(),
            attachment_path=attachment_path,
            is_internal=is_internal,
            created_at=datetime.now(),
        )


@dataclass
class SupportTicket(AggregateRoot[int]):
    """
    Support ticket submitted by an employee.

    Tracks IT, HR, and other support requests.
    """

    ticket_number: str
    employee_id: int
    category: TicketCategory
    priority: TicketPriority
    subject: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    assigned_to: Optional[int] = None
    messages: List[TicketMessage] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        ticket_number: str,
        employee_id: int,
        category: TicketCategory,
        priority: TicketPriority,
        subject: str,
        description: str,
    ) -> "SupportTicket":
        """Create a new support ticket."""
        if not subject or not subject.strip():
            raise ValueError("Subject cannot be empty")
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")

        return cls(
            id=None,
            ticket_number=ticket_number,
            employee_id=employee_id,
            category=category,
            priority=priority,
            subject=subject.strip(),
            description=description.strip(),
            status=TicketStatus.OPEN,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def add_message(self, message: TicketMessage) -> None:
        """Add a message to the ticket."""
        message.ticket_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.now()

        # Auto-reopen if employee replies to resolved ticket
        if (
            not message.is_internal
            and message.sender_id == self.employee_id
            and self.status == TicketStatus.RESOLVED
        ):
            self.status = TicketStatus.OPEN

    def assign_to(self, assignee_id: int) -> None:
        """Assign ticket to a staff member."""
        self.assigned_to = assignee_id
        if self.status == TicketStatus.OPEN:
            self.status = TicketStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def mark_waiting(self) -> None:
        """Mark ticket as waiting for response."""
        self.status = TicketStatus.WAITING
        self.updated_at = datetime.now()

    def resolve(self) -> None:
        """Mark ticket as resolved."""
        self.status = TicketStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()

    def close(self) -> None:
        """Close the ticket."""
        if not self.status.can_close:
            raise ValueError(
                "Ticket must be resolved or waiting to be closed"
            )

        self.status = TicketStatus.CLOSED
        self.closed_at = datetime.now()
        self.updated_at = datetime.now()

    def reopen(self) -> None:
        """Reopen a closed ticket."""
        if not self.status.can_reopen:
            raise ValueError("Only closed tickets can be reopened")

        self.status = TicketStatus.OPEN
        self.closed_at = None
        self.resolved_at = None
        self.updated_at = datetime.now()

    @property
    def is_open(self) -> bool:
        return self.status.is_open

    @property
    def is_closed(self) -> bool:
        return self.status.is_closed

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def public_messages(self) -> List[TicketMessage]:
        """Get non-internal messages."""
        return [m for m in self.messages if not m.is_internal]

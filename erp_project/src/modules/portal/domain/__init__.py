"""
Portal domain layer.

Contains entities, value objects, events, and domain services.
"""

from modules.portal.domain.entities import (
    ExpenseClaim,
    SupportTicket,
    TicketMessage,
    Notification,
    Document,
    DocumentAcknowledgement,
    DocumentCategory,
)
from modules.portal.domain.value_objects import (
    ExpenseStatus,
    TicketStatus,
    TicketCategory,
    TicketPriority,
    NotificationType,
    DocumentVisibility,
    QRToken,
    ExpenseAmount,
    TicketNumber,
    ClockStatus,
)

__all__ = [
    # Entities
    "ExpenseClaim",
    "SupportTicket",
    "TicketMessage",
    "Notification",
    "Document",
    "DocumentAcknowledgement",
    "DocumentCategory",
    # Value Objects
    "ExpenseStatus",
    "TicketStatus",
    "TicketCategory",
    "TicketPriority",
    "NotificationType",
    "DocumentVisibility",
    "QRToken",
    "ExpenseAmount",
    "TicketNumber",
    "ClockStatus",
]

"""
Portal module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.portal.infrastructure.persistence.models import (
    AttendanceQRToken,
    Document,
    DocumentAcknowledgement,
    DocumentCategory,
    ExpenseCategory,
    ExpenseClaim,
    Notification,
    SupportTicket,
    TicketMessage,
)

__all__ = [
    "ExpenseCategory",
    "ExpenseClaim",
    "SupportTicket",
    "TicketMessage",
    "Notification",
    "DocumentCategory",
    "Document",
    "DocumentAcknowledgement",
    "AttendanceQRToken",
]

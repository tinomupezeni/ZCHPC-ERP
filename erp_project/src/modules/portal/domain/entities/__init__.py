"""
Portal domain entities.
"""

from modules.portal.domain.entities.expense_claim import ExpenseClaim
from modules.portal.domain.entities.support_ticket import (
    SupportTicket,
    TicketMessage,
)
from modules.portal.domain.entities.notification import Notification
from modules.portal.domain.entities.document import (
    Document,
    DocumentAcknowledgement,
    DocumentCategory,
)

__all__ = [
    "ExpenseClaim",
    "SupportTicket",
    "TicketMessage",
    "Notification",
    "Document",
    "DocumentAcknowledgement",
    "DocumentCategory",
]

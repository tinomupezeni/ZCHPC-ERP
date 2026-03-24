"""
Repository interfaces for the portal module.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from modules.portal.domain.entities import (
    ExpenseClaim,
    SupportTicket,
    Notification,
    Document,
    DocumentCategory,
)
from modules.portal.domain.value_objects import (
    ExpenseStatus,
    TicketStatus,
    TicketCategory,
    NotificationType,
)


class IExpenseClaimRepository(ABC):
    """Interface for expense claim repository."""

    @abstractmethod
    def save(self, claim: ExpenseClaim) -> ExpenseClaim:
        """Save an expense claim."""
        ...

    @abstractmethod
    def get_by_id(self, claim_id: int) -> Optional[ExpenseClaim]:
        """Get a claim by ID."""
        ...

    @abstractmethod
    def get_by_employee(
        self,
        employee_id: int,
        status: Optional[ExpenseStatus] = None,
    ) -> List[ExpenseClaim]:
        """Get claims by employee with optional status filter."""
        ...

    @abstractmethod
    def get_pending_review(self) -> List[ExpenseClaim]:
        """Get claims pending review."""
        ...

    @abstractmethod
    def delete(self, claim_id: int) -> bool:
        """Delete a claim (only if draft)."""
        ...


class ISupportTicketRepository(ABC):
    """Interface for support ticket repository."""

    @abstractmethod
    def save(self, ticket: SupportTicket) -> SupportTicket:
        """Save a support ticket."""
        ...

    @abstractmethod
    def get_by_id(self, ticket_id: int) -> Optional[SupportTicket]:
        """Get a ticket by ID with messages."""
        ...

    @abstractmethod
    def get_by_ticket_number(self, ticket_number: str) -> Optional[SupportTicket]:
        """Get a ticket by ticket number."""
        ...

    @abstractmethod
    def get_by_employee(
        self,
        employee_id: int,
        status: Optional[TicketStatus] = None,
        category: Optional[TicketCategory] = None,
    ) -> List[SupportTicket]:
        """Get tickets by employee with optional filters."""
        ...

    @abstractmethod
    def get_open_tickets(self) -> List[SupportTicket]:
        """Get all open tickets."""
        ...

    @abstractmethod
    def get_next_ticket_number(self) -> str:
        """Generate the next ticket number."""
        ...


class INotificationRepository(ABC):
    """Interface for notification repository."""

    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        ...

    @abstractmethod
    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get a notification by ID."""
        ...

    @abstractmethod
    def get_by_employee(
        self,
        employee_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """Get notifications for an employee."""
        ...

    @abstractmethod
    def get_unread_count(self, employee_id: int) -> int:
        """Get count of unread notifications."""
        ...

    @abstractmethod
    def mark_all_read(self, employee_id: int) -> int:
        """Mark all notifications as read. Returns count updated."""
        ...


class IDocumentRepository(ABC):
    """Interface for document repository."""

    @abstractmethod
    def save(self, document: Document) -> Document:
        """Save a document."""
        ...

    @abstractmethod
    def get_by_id(self, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        ...

    @abstractmethod
    def get_accessible_documents(
        self,
        employee_id: int,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[Document]:
        """Get documents accessible by an employee."""
        ...

    @abstractmethod
    def get_pending_acknowledgements(
        self,
        employee_id: int,
    ) -> List[Document]:
        """Get documents requiring acknowledgement from employee."""
        ...


class IDocumentCategoryRepository(ABC):
    """Interface for document category repository."""

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[DocumentCategory]:
        """Get all document categories."""
        ...

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[DocumentCategory]:
        """Get a category by ID."""
        ...


class IExpenseCategoryRepository(ABC):
    """Interface for expense category repository."""

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[dict]:
        """Get all expense categories."""
        ...

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[dict]:
        """Get a category by ID."""
        ...


class IQRTokenRepository(ABC):
    """Interface for QR token repository."""

    @abstractmethod
    def get_current_token(self) -> Optional[str]:
        """Get the current active QR token."""
        ...

    @abstractmethod
    def create_token(self, token: str, expires_at: datetime) -> None:
        """Create a new QR token."""
        ...

    @abstractmethod
    def verify_token(self, token: str) -> bool:
        """Verify if a token is valid."""
        ...

    @abstractmethod
    def increment_usage(self, token: str) -> None:
        """Increment token usage count."""
        ...

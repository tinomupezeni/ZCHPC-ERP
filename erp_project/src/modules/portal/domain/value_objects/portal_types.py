"""
Value objects for the portal module.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional
import secrets

from shared.domain.base import ValueObject


class ExpenseStatus(str, Enum):
    """Status of an expense claim."""

    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "UnderReview"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID = "Paid"

    @property
    def is_draft(self) -> bool:
        return self == ExpenseStatus.DRAFT

    @property
    def is_submitted(self) -> bool:
        return self == ExpenseStatus.SUBMITTED

    @property
    def is_approved(self) -> bool:
        return self == ExpenseStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self == ExpenseStatus.REJECTED

    @property
    def is_paid(self) -> bool:
        return self == ExpenseStatus.PAID

    @property
    def can_edit(self) -> bool:
        return self == ExpenseStatus.DRAFT

    @property
    def can_submit(self) -> bool:
        return self == ExpenseStatus.DRAFT

    @property
    def can_cancel(self) -> bool:
        return self in (ExpenseStatus.DRAFT, ExpenseStatus.SUBMITTED)


class TicketStatus(str, Enum):
    """Status of a support ticket."""

    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    WAITING = "Waiting"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

    @property
    def is_open(self) -> bool:
        return self == TicketStatus.OPEN

    @property
    def is_in_progress(self) -> bool:
        return self == TicketStatus.IN_PROGRESS

    @property
    def is_resolved(self) -> bool:
        return self == TicketStatus.RESOLVED

    @property
    def is_closed(self) -> bool:
        return self == TicketStatus.CLOSED

    @property
    def can_close(self) -> bool:
        return self in (TicketStatus.RESOLVED, TicketStatus.WAITING)

    @property
    def can_reopen(self) -> bool:
        return self == TicketStatus.CLOSED


class TicketCategory(str, Enum):
    """Category of a support ticket."""

    IT = "IT"
    HR = "HR"
    FACILITIES = "Facilities"
    FINANCE = "Finance"
    OTHER = "Other"


class TicketPriority(str, Enum):
    """Priority of a support ticket."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class NotificationType(str, Enum):
    """Type of notification."""

    LEAVE_APPROVED = "leave_approved"
    LEAVE_REJECTED = "leave_rejected"
    LEAVE_REQUEST = "leave_request"
    EXPENSE_APPROVED = "expense_approved"
    EXPENSE_REJECTED = "expense_rejected"
    TICKET_UPDATE = "ticket_update"
    TICKET_RESOLVED = "ticket_resolved"
    PAYSLIP_AVAILABLE = "payslip_available"
    ANNOUNCEMENT = "announcement"
    SYSTEM = "system"


class DocumentVisibility(str, Enum):
    """Visibility level for a document."""

    ALL = "all"
    DEPARTMENT = "department"
    SPECIFIC = "specific"


@dataclass(frozen=True)
class QRToken(ValueObject):
    """Value object representing a QR attendance token."""

    token: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.token or len(self.token) < 32:
            raise ValueError("Token must be at least 32 characters")

    @classmethod
    def generate(cls, validity_seconds: int = 30) -> "QRToken":
        """Generate a new secure QR token."""
        token = secrets.token_urlsafe(48)
        expires_at = datetime.now() + timedelta(seconds=validity_seconds)
        return cls(token=token, expires_at=expires_at)

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_expired


@dataclass(frozen=True)
class ExpenseAmount(ValueObject):
    """Value object for expense amounts with currency."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        if self.currency not in ("USD", "ZiG"):
            raise ValueError("Currency must be USD or ZiG")


@dataclass(frozen=True)
class TicketNumber(ValueObject):
    """Value object for ticket numbers."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.startswith("TKT-"):
            raise ValueError("Invalid ticket number format")

    @classmethod
    def generate(cls, date: datetime, sequence: int) -> "TicketNumber":
        """Generate a ticket number."""
        date_str = date.strftime("%Y%m%d")
        return cls(value=f"TKT-{date_str}-{sequence:04d}")


@dataclass(frozen=True)
class ClockStatus(ValueObject):
    """Value object representing today's clock status."""

    is_clocked_in: bool
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None

    @property
    def worked_hours(self) -> Optional[float]:
        """Calculate hours worked if both times are present."""
        if self.clock_in_time and self.clock_out_time:
            delta = self.clock_out_time - self.clock_in_time
            return delta.total_seconds() / 3600
        return None

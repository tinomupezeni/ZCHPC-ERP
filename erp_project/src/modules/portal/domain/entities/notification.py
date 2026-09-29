"""
Notification entity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shared.domain.base import Entity
from modules.portal.domain.value_objects import NotificationType


@dataclass
class Notification(Entity[int]):
    """
    Notification for an employee.

    Used to alert employees about events like leave approvals,
    payslip availability, etc.
    """

    employee_id: int
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        # Entity[int].__init__ (which sets self._id) is entirely replaced by
        # this dataclass's generated __init__, since Entity itself isn't a
        # dataclass - without this, self.id would raise AttributeError for
        # every notification built via create() below. Matches the same
        # defensive pattern used by modules.procurement's dataclass entities.
        if not hasattr(self, "_id"):
            self._id = None

    @classmethod
    def create(
        cls,
        employee_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_object_type: Optional[str] = None,
        related_object_id: Optional[int] = None,
    ) -> "Notification":
        """Create a new notification."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        return cls(
            employee_id=employee_id,
            notification_type=notification_type,
            title=title.strip(),
            message=message.strip(),
            is_read=False,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            created_at=datetime.now(),
        )

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now()

    def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        self.is_read = False
        self.read_at = None

    @classmethod
    def leave_approved(
        cls,
        employee_id: int,
        leave_request_id: int,
    ) -> "Notification":
        """Create a leave approved notification."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.LEAVE_APPROVED,
            title="Leave Request Approved",
            message="Your leave request has been approved.",
            related_object_type="leave_request",
            related_object_id=leave_request_id,
        )

    @classmethod
    def leave_rejected(
        cls,
        employee_id: int,
        leave_request_id: int,
        reason: Optional[str] = None,
    ) -> "Notification":
        """Create a leave rejected notification."""
        message = "Your leave request has been rejected."
        if reason:
            message = f"{message} Reason: {reason}"

        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.LEAVE_REJECTED,
            title="Leave Request Rejected",
            message=message,
            related_object_type="leave_request",
            related_object_id=leave_request_id,
        )

    @classmethod
    def expense_approved(
        cls,
        employee_id: int,
        expense_id: int,
    ) -> "Notification":
        """Create an expense approved notification."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.EXPENSE_APPROVED,
            title="Expense Claim Approved",
            message="Your expense claim has been approved.",
            related_object_type="expense_claim",
            related_object_id=expense_id,
        )

    @classmethod
    def expense_rejected(
        cls,
        employee_id: int,
        expense_id: int,
        reason: Optional[str] = None,
    ) -> "Notification":
        """Create an expense rejected notification."""
        message = "Your expense claim has been rejected."
        if reason:
            message = f"{message} Reason: {reason}"

        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.EXPENSE_REJECTED,
            title="Expense Claim Rejected",
            message=message,
            related_object_type="expense_claim",
            related_object_id=expense_id,
        )

    @classmethod
    def payslip_available(
        cls,
        employee_id: int,
        payslip_id: int,
        period: str,
    ) -> "Notification":
        """Create a payslip available notification."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.PAYSLIP_AVAILABLE,
            title="Payslip Available",
            message=f"Your payslip for {period} is now available.",
            related_object_type="payslip",
            related_object_id=payslip_id,
        )

    @classmethod
    def ticket_update(
        cls,
        employee_id: int,
        ticket_id: int,
        ticket_number: str,
    ) -> "Notification":
        """Create a ticket update notification."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.TICKET_UPDATE,
            title="Ticket Updated",
            message=f"Ticket {ticket_number} has been updated.",
            related_object_type="support_ticket",
            related_object_id=ticket_id,
        )

    @classmethod
    def purchase_request_rejected(
        cls,
        employee_id: int,
        request_id: int,
        requisition_number: str,
        reason: str,
    ) -> "Notification":
        """
        Create a purchase request rejected notification (Slice 3).

        Never carries GL/budget code data - only the requisition number and
        the rejection reason, both already employee-facing everywhere else in
        the Purchase Request workflow.
        """
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.PURCHASE_REQUEST_REJECTED,
            title="Purchase Request Rejected",
            message=(
                f"Your purchase requisition {requisition_number} was rejected. "
                f"Reason: {reason}"
            ),
            related_object_type="purchase_request",
            related_object_id=request_id,
        )

    @classmethod
    def purchase_request_processed(
        cls,
        employee_id: int,
        request_id: int,
        requisition_number: str,
    ) -> "Notification":
        """Create a purchase request processed notification (Slice 3) - a positive completion notice."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.PURCHASE_REQUEST_PROCESSED,
            title="Purchase Request Processed",
            message=(
                f"Your purchase requisition {requisition_number} has been "
                f"processed by Procurement."
            ),
            related_object_type="purchase_request",
            related_object_id=request_id,
        )

    @classmethod
    def purchase_request_awaiting_review(
        cls,
        employee_id: int,
        request_id: int,
        requisition_number: str,
        notification_type: NotificationType,
        stage_label: str,
    ) -> "Notification":
        """
        Create a "this purchase request now needs your review" notification
        (F27), for whichever stage's reviewer the caller has already
        resolved.

        One factory shared by every forward-workflow stage rather than five
        near-identical ones: notification_type and stage_label are supplied
        by modules.portal.event_handlers.handle_purchase_request_awaiting_review,
        which is the one place that maps a PurchaseRequestAwaitingReview
        event's new_status to a concrete recipient, notification_type and
        stage label. Like every other purchase_request_* notification here,
        this never carries GL/budget code data - only the requisition number.
        """
        return cls.create(
            employee_id=employee_id,
            notification_type=notification_type,
            title=f"Purchase Request Awaiting {stage_label} Review",
            message=(
                f"Purchase requisition {requisition_number} is now awaiting "
                f"{stage_label} review."
            ),
            related_object_type="purchase_request",
            related_object_id=request_id,
        )

    @classmethod
    def purchase_request_corrected(
        cls,
        employee_id: int,
        request_id: int,
        requisition_number: str,
    ) -> "Notification":
        """
        Create a purchase-request-corrected notification for the department
        head (F19).

        Unlike every other purchase_request_* notification, employee_id here
        is the department head, not the requester - a rejected request that
        gets corrected and resubmitted returns to PENDING_DEPARTMENT_HEAD via
        the normal submit flow, and the department head must be told
        explicitly that this is a correction awaiting re-approval, not a
        first-time submission they might otherwise approve on the assumption
        nothing has changed since they last saw it.
        """
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.PURCHASE_REQUEST_CORRECTED,
            title="Purchase Request Corrected",
            message=(
                f"{requisition_number} has been corrected and requires your re-approval."
            ),
            related_object_type="purchase_request",
            related_object_id=request_id,
        )

    @classmethod
    def announcement(
        cls,
        employee_id: int,
        title: str,
        message: str,
    ) -> "Notification":
        """Create an announcement notification."""
        return cls.create(
            employee_id=employee_id,
            notification_type=NotificationType.ANNOUNCEMENT,
            title=title,
            message=message,
        )

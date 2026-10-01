"""
Tests for portal entities.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from modules.portal.domain.entities import (
    ExpenseClaim,
    SupportTicket,
    TicketMessage,
    Notification,
    Document,
    DocumentCategory,
)
from modules.portal.domain.value_objects import (
    ExpenseStatus,
    TicketStatus,
    TicketCategory,
    TicketPriority,
    NotificationType,
    DocumentVisibility,
)


class TestExpenseClaim:
    """Tests for ExpenseClaim entity."""

    def test_create_expense_claim(self):
        claim = ExpenseClaim.create(
            employee_id=1,
            category_id=1,
            title="Office Supplies",
            description="Pens and notebooks",
            amount=Decimal("50.00"),
        )
        assert claim.title == "Office Supplies"
        assert claim.status == ExpenseStatus.DRAFT
        assert claim.currency == "USD"

    def test_submit_claim(self):
        claim = ExpenseClaim.create(
            employee_id=1,
            category_id=1,
            title="Office Supplies",
            description="Pens",
            amount=Decimal("50.00"),
        )
        claim.submit()
        assert claim.status == ExpenseStatus.SUBMITTED
        assert claim.submitted_at is not None

    def test_approve_claim(self):
        claim = ExpenseClaim.create(
            employee_id=1,
            category_id=1,
            title="Office Supplies",
            description="Pens",
            amount=Decimal("50.00"),
        )
        claim.submit()
        claim.approve(reviewer_id=2, notes="Approved for payment")
        assert claim.status == ExpenseStatus.APPROVED
        assert claim.reviewed_by == 2

    def test_reject_claim(self):
        claim = ExpenseClaim.create(
            employee_id=1,
            category_id=1,
            title="Office Supplies",
            description="Pens",
            amount=Decimal("50.00"),
        )
        claim.submit()
        claim.reject(reviewer_id=2, reason="Not approved")
        assert claim.status == ExpenseStatus.REJECTED
        assert claim.review_notes == "Not approved"

    def test_cannot_edit_submitted_claim(self):
        claim = ExpenseClaim.create(
            employee_id=1,
            category_id=1,
            title="Office Supplies",
            description="Pens",
            amount=Decimal("50.00"),
        )
        claim.submit()
        with pytest.raises(ValueError):
            claim.update(title="Updated Title")


class TestSupportTicket:
    """Tests for SupportTicket entity."""

    def test_create_ticket(self):
        ticket = SupportTicket.create(
            ticket_number="TKT-20240101-0001",
            employee_id=1,
            category=TicketCategory.IT,
            priority=TicketPriority.MEDIUM,
            subject="Computer issue",
            description="My computer won't start",
        )
        assert ticket.subject == "Computer issue"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.category == TicketCategory.IT

    def test_add_message(self):
        ticket = SupportTicket.create(
            ticket_number="TKT-20240101-0001",
            employee_id=1,
            category=TicketCategory.IT,
            priority=TicketPriority.MEDIUM,
            subject="Computer issue",
            description="My computer won't start",
        )
        message = TicketMessage.create(
            sender_id=2,
            message="Have you tried turning it off and on again?",
        )
        ticket.add_message(message)
        assert len(ticket.messages) == 1

    def test_resolve_ticket(self):
        ticket = SupportTicket.create(
            ticket_number="TKT-20240101-0001",
            employee_id=1,
            category=TicketCategory.IT,
            priority=TicketPriority.MEDIUM,
            subject="Computer issue",
            description="My computer won't start",
        )
        ticket.resolve()
        assert ticket.status == TicketStatus.RESOLVED
        assert ticket.resolved_at is not None

    def test_close_resolved_ticket(self):
        ticket = SupportTicket.create(
            ticket_number="TKT-20240101-0001",
            employee_id=1,
            category=TicketCategory.IT,
            priority=TicketPriority.MEDIUM,
            subject="Computer issue",
            description="My computer won't start",
        )
        ticket.resolve()
        ticket.close()
        assert ticket.status == TicketStatus.CLOSED

    def test_cannot_close_open_ticket(self):
        ticket = SupportTicket.create(
            ticket_number="TKT-20240101-0001",
            employee_id=1,
            category=TicketCategory.IT,
            priority=TicketPriority.MEDIUM,
            subject="Computer issue",
            description="My computer won't start",
        )
        with pytest.raises(ValueError):
            ticket.close()


class TestNotification:
    """Tests for Notification entity."""

    def test_create_notification(self):
        notification = Notification.create(
            employee_id=1,
            notification_type=NotificationType.ANNOUNCEMENT,
            title="Company Meeting",
            message="All hands meeting tomorrow",
        )
        assert notification.title == "Company Meeting"
        assert not notification.is_read

    def test_mark_as_read(self):
        notification = Notification.create(
            employee_id=1,
            notification_type=NotificationType.ANNOUNCEMENT,
            title="Company Meeting",
            message="All hands meeting tomorrow",
        )
        notification.mark_as_read()
        assert notification.is_read
        assert notification.read_at is not None

    def test_leave_approved_notification(self):
        notification = Notification.leave_approved(
            employee_id=1,
            leave_request_id=10,
        )
        assert notification.notification_type == NotificationType.LEAVE_APPROVED
        assert notification.related_object_type == "leave_request"
        assert notification.related_object_id == 10

    def test_payslip_available_notification(self):
        notification = Notification.payslip_available(
            employee_id=1,
            payslip_id=5,
            period="January 2024",
        )
        assert notification.notification_type == NotificationType.PAYSLIP_AVAILABLE
        assert "January 2024" in notification.message


class TestDocument:
    """Tests for Document entity."""

    def test_create_document(self):
        doc = Document.create(
            category_id=1,
            title="Employee Handbook",
            description="Company policies",
            file_path="/docs/handbook.pdf",
            file_type="pdf",
            file_size=1024000,
            uploaded_by=1,
        )
        assert doc.title == "Employee Handbook"
        assert doc.visibility == DocumentVisibility.ALL
        assert doc.is_active

    def test_can_access_all_visibility(self):
        doc = Document.create(
            category_id=1,
            title="Employee Handbook",
            description="Company policies",
            file_path="/docs/handbook.pdf",
            file_type="pdf",
            file_size=1024000,
            uploaded_by=1,
            visibility=DocumentVisibility.ALL,
        )
        assert doc.can_access(employee_id=999)

    def test_can_access_department_visibility(self):
        doc = Document.create(
            category_id=1,
            title="IT Policies",
            description="IT department policies",
            file_path="/docs/it-policies.pdf",
            file_type="pdf",
            file_size=512000,
            uploaded_by=1,
            visibility=DocumentVisibility.DEPARTMENT,
        )
        doc.add_department(5)

        assert doc.can_access(employee_id=1, employee_department_id=5)
        assert not doc.can_access(employee_id=1, employee_department_id=10)

    def test_acknowledge_document(self):
        doc = Document.create(
            category_id=1,
            title="Code of Conduct",
            description="Company code of conduct",
            file_path="/docs/code.pdf",
            file_type="pdf",
            file_size=256000,
            uploaded_by=1,
            requires_acknowledgement=True,
        )
        doc._id = 1  # Simulate saved document

        ack = doc.acknowledge(employee_id=5, ip_address="192.168.1.1")
        assert doc.has_acknowledged(5)
        assert ack.ip_address == "192.168.1.1"

    def test_cannot_acknowledge_twice(self):
        doc = Document.create(
            category_id=1,
            title="Code of Conduct",
            description="Company code of conduct",
            file_path="/docs/code.pdf",
            file_type="pdf",
            file_size=256000,
            uploaded_by=1,
            requires_acknowledgement=True,
        )
        doc._id = 1

        doc.acknowledge(employee_id=5)
        with pytest.raises(ValueError):
            doc.acknowledge(employee_id=5)

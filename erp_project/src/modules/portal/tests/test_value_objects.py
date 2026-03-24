"""
Tests for portal value objects.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

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


class TestExpenseStatus:
    """Tests for ExpenseStatus enum."""

    def test_draft_status(self):
        status = ExpenseStatus.DRAFT
        assert status.is_draft
        assert status.can_edit
        assert status.can_submit
        assert status.can_cancel

    def test_submitted_status(self):
        status = ExpenseStatus.SUBMITTED
        assert status.is_submitted
        assert not status.can_edit
        assert status.can_cancel

    def test_approved_status(self):
        status = ExpenseStatus.APPROVED
        assert status.is_approved
        assert not status.can_edit
        assert not status.can_cancel


class TestTicketStatus:
    """Tests for TicketStatus enum."""

    def test_open_status(self):
        status = TicketStatus.OPEN
        assert status.is_open
        assert not status.can_close

    def test_resolved_status(self):
        status = TicketStatus.RESOLVED
        assert status.is_resolved
        assert status.can_close

    def test_closed_status(self):
        status = TicketStatus.CLOSED
        assert status.is_closed
        assert status.can_reopen


class TestQRToken:
    """Tests for QRToken value object."""

    def test_generate_token(self):
        token = QRToken.generate(validity_seconds=30)
        assert len(token.token) >= 32
        assert token.expires_at > datetime.now()
        assert token.is_valid

    def test_expired_token(self):
        token = QRToken(
            token="a" * 32,
            expires_at=datetime.now() - timedelta(seconds=1)
        )
        assert token.is_expired
        assert not token.is_valid

    def test_short_token_raises(self):
        with pytest.raises(ValueError):
            QRToken(token="short", expires_at=datetime.now())


class TestExpenseAmount:
    """Tests for ExpenseAmount value object."""

    def test_create_amount(self):
        amount = ExpenseAmount(amount=Decimal("100.00"))
        assert amount.amount == Decimal("100.00")
        assert amount.currency == "USD"

    def test_amount_with_zig(self):
        amount = ExpenseAmount(amount=Decimal("100.00"), currency="ZiG")
        assert amount.currency == "ZiG"

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError):
            ExpenseAmount(amount=Decimal("-10.00"))

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError):
            ExpenseAmount(amount=Decimal("100.00"), currency="EUR")


class TestTicketNumber:
    """Tests for TicketNumber value object."""

    def test_create_ticket_number(self):
        ticket_num = TicketNumber(value="TKT-20240101-0001")
        assert ticket_num.value == "TKT-20240101-0001"

    def test_generate_ticket_number(self):
        dt = datetime(2024, 1, 15)
        ticket_num = TicketNumber.generate(dt, 42)
        assert ticket_num.value == "TKT-20240115-0042"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            TicketNumber(value="INVALID-001")


class TestClockStatus:
    """Tests for ClockStatus value object."""

    def test_not_clocked_in(self):
        status = ClockStatus(is_clocked_in=False)
        assert not status.is_clocked_in
        assert status.worked_hours is None

    def test_clocked_in(self):
        clock_in = datetime.now() - timedelta(hours=4)
        status = ClockStatus(
            is_clocked_in=True,
            clock_in_time=clock_in,
        )
        assert status.is_clocked_in
        assert status.worked_hours is None  # Not clocked out yet

    def test_clocked_out(self):
        clock_in = datetime.now() - timedelta(hours=8)
        clock_out = datetime.now()
        status = ClockStatus(
            is_clocked_in=False,
            clock_in_time=clock_in,
            clock_out_time=clock_out,
        )
        assert not status.is_clocked_in
        assert status.worked_hours is not None
        assert 7.9 < status.worked_hours < 8.1

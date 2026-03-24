"""
Tests for leave entities.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from modules.leave.domain.entities import LeaveBalance, LeaveRequest, LeaveType
from modules.leave.domain.value_objects import LeaveEntitlement, LeavePeriod, LeaveStatus


class TestLeaveType:
    """Tests for LeaveType entity."""

    def test_create_leave_type(self):
        """Test creating a leave type."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
            is_active=True,
        )
        assert leave_type.id == 1
        assert leave_type.name == "Annual Leave"
        assert leave_type.default_days_allowed == 20
        assert leave_type.is_active is True

    def test_rename_leave_type(self):
        """Test renaming a leave type."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
        )
        leave_type.rename("Paid Time Off")
        assert leave_type.name == "Paid Time Off"

    def test_rename_empty_name_raises_error(self):
        """Test that renaming with empty name raises error."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
        )
        with pytest.raises(ValueError):
            leave_type.rename("")

    def test_update_default_days(self):
        """Test updating default days allowed."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
        )
        leave_type.update_default_days(25)
        assert leave_type.default_days_allowed == 25

    def test_update_default_days_negative_raises_error(self):
        """Test that negative default days raises error."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
        )
        with pytest.raises(ValueError):
            leave_type.update_default_days(-5)

    def test_deactivate_leave_type(self):
        """Test deactivating a leave type."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
            is_active=True,
        )
        leave_type.deactivate()
        assert leave_type.is_active is False

    def test_activate_leave_type(self):
        """Test activating a leave type."""
        leave_type = LeaveType(
            id=1,
            name="Annual Leave",
            default_days_allowed=20,
            is_active=False,
        )
        leave_type.activate()
        assert leave_type.is_active is True


class TestLeaveBalance:
    """Tests for LeaveBalance entity."""

    def test_create_leave_balance(self):
        """Test creating a leave balance."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        assert balance.id == 1
        assert balance.employee_id == 100
        assert balance.leave_type_id == 1
        assert balance.year == 2024
        assert balance.entitled_days == Decimal("20")
        assert balance.used_days == Decimal("5")
        assert balance.remaining_days == Decimal("15")

    def test_deduct_days(self):
        """Test deducting days from balance."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        balance.deduct(3)
        assert balance.used_days == Decimal("8")
        assert balance.remaining_days == Decimal("12")

    def test_restore_days(self):
        """Test restoring days to balance."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("10"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        balance.restore(3)
        assert balance.used_days == Decimal("7")
        assert balance.remaining_days == Decimal("13")

    def test_adjust_entitlement(self):
        """Test adjusting entitled days."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        balance.adjust_entitlement(Decimal("25"))
        assert balance.entitled_days == Decimal("25")
        assert balance.remaining_days == Decimal("20")

    def test_has_sufficient_balance(self):
        """Test checking sufficient balance."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        assert balance.has_sufficient_balance(10) is True
        assert balance.has_sufficient_balance(15) is True
        assert balance.has_sufficient_balance(16) is False

    def test_usage_percentage(self):
        """Test usage percentage calculation."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("10"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )
        assert balance.usage_percentage == Decimal("50.00")


class TestLeaveRequest:
    """Tests for LeaveRequest entity."""

    def test_create_leave_request(self):
        """Test creating a leave request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
            reason="Family vacation",
        )
        assert request.id == 1
        assert request.employee_id == 100
        assert request.leave_type_id == 1
        assert request.start_date == date(2024, 1, 15)
        assert request.end_date == date(2024, 1, 19)
        assert request.days == 5
        assert request.reason == "Family vacation"
        assert request.status == LeaveStatus.PENDING

    def test_approve_request(self):
        """Test approving a leave request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.approve(reviewer_id=200)
        assert request.status == LeaveStatus.APPROVED
        assert request.reviewed_by_id == 200
        assert request.reviewed_at is not None

    def test_reject_request(self):
        """Test rejecting a leave request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.reject(reviewer_id=200)
        assert request.status == LeaveStatus.REJECTED
        assert request.reviewed_by_id == 200
        assert request.reviewed_at is not None

    def test_cancel_pending_request(self):
        """Test cancelling a pending request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.cancel()
        assert request.status == LeaveStatus.CANCELLED

    def test_cancel_approved_request(self):
        """Test cancelling an approved request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.approve(reviewer_id=200)
        request.cancel()
        assert request.status == LeaveStatus.CANCELLED

    def test_cannot_approve_already_approved(self):
        """Test that approved request cannot be approved again."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.approve(reviewer_id=200)
        with pytest.raises(ValueError):
            request.approve(reviewer_id=201)

    def test_cannot_reject_approved(self):
        """Test that approved request cannot be rejected."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.approve(reviewer_id=200)
        with pytest.raises(ValueError):
            request.reject(reviewer_id=201)

    def test_cannot_cancel_rejected(self):
        """Test that rejected request cannot be cancelled."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        request.reject(reviewer_id=200)
        with pytest.raises(ValueError):
            request.cancel()

    def test_can_review_pending_request(self):
        """Test can_review for pending request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        assert request.can_review is True

    def test_can_cancel_pending_request(self):
        """Test can_cancel for pending request."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        assert request.can_cancel is True

    def test_overlaps_with(self):
        """Test overlap detection between requests."""
        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 18),
            end_date=date(2024, 1, 22),
        )
        request1 = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period1,
        )
        request2 = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period2,
        )
        assert request1.overlaps_with(request2) is True

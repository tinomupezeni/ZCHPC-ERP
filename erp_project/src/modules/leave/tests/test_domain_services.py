"""
Tests for leave domain services.
"""

from datetime import date
from decimal import Decimal

import pytest

from modules.leave.domain.entities import LeaveBalance, LeaveRequest
from modules.leave.domain.services import (
    DefaultLeaveApprovalPolicy,
    DefaultLeaveYearService,
    LeaveBalanceCalculator,
    LeaveConflictDetector,
)
from modules.leave.domain.value_objects import LeaveEntitlement, LeavePeriod, LeaveStatus


class TestLeaveConflictDetector:
    """Tests for LeaveConflictDetector service."""

    def test_no_conflicts_with_empty_list(self):
        """Test no conflicts when no existing requests."""
        detector = LeaveConflictDetector()
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
        conflicts = detector.find_conflicts(request, [])
        assert len(conflicts) == 0

    def test_detects_overlapping_conflict(self):
        """Test detecting overlapping request."""
        detector = LeaveConflictDetector()

        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 18),
            end_date=date(2024, 1, 22),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period1,
        )
        existing_request = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period2,
            status=LeaveStatus.APPROVED,
        )

        conflicts = detector.find_conflicts(new_request, [existing_request])
        assert len(conflicts) == 1
        assert conflicts[0].id == 2

    def test_ignores_cancelled_requests(self):
        """Test that cancelled requests are not considered conflicts."""
        detector = LeaveConflictDetector()

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        cancelled_request = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period,
            status=LeaveStatus.CANCELLED,
        )

        conflicts = detector.find_conflicts(new_request, [cancelled_request])
        assert len(conflicts) == 0

    def test_ignores_rejected_requests(self):
        """Test that rejected requests are not considered conflicts."""
        detector = LeaveConflictDetector()

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        rejected_request = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period,
            status=LeaveStatus.REJECTED,
        )

        conflicts = detector.find_conflicts(new_request, [rejected_request])
        assert len(conflicts) == 0

    def test_ignores_other_employees_requests(self):
        """Test that other employees' requests are not considered conflicts."""
        detector = LeaveConflictDetector()

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        other_employee_request = LeaveRequest(
            id=2,
            employee_id=200,  # Different employee
            leave_type_id=1,
            period=period,
            status=LeaveStatus.APPROVED,
        )

        conflicts = detector.find_conflicts(new_request, [other_employee_request])
        assert len(conflicts) == 0

    def test_has_conflict_returns_true(self):
        """Test has_conflict returns true when conflicts exist."""
        detector = LeaveConflictDetector()

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
        )
        existing_request = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period,
            status=LeaveStatus.APPROVED,
        )

        assert detector.has_conflict(new_request, [existing_request]) is True

    def test_has_conflict_returns_false(self):
        """Test has_conflict returns false when no conflicts."""
        detector = LeaveConflictDetector()

        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 25),
            end_date=date(2024, 1, 29),
        )

        new_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period1,
        )
        existing_request = LeaveRequest(
            id=2,
            employee_id=100,
            leave_type_id=1,
            period=period2,
            status=LeaveStatus.APPROVED,
        )

        assert detector.has_conflict(new_request, [existing_request]) is False


class TestLeaveBalanceCalculator:
    """Tests for LeaveBalanceCalculator service."""

    def test_calculate_available_with_no_pending(self):
        """Test calculating available days with no pending requests."""
        calculator = LeaveBalanceCalculator()

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

        available = calculator.calculate_available_days(balance, [])
        assert available == Decimal("15")

    def test_calculate_available_with_pending_requests(self):
        """Test calculating available days with pending requests."""
        calculator = LeaveBalanceCalculator()

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

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 17),  # 3 days
        )
        pending_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,  # Same leave type
            period=period,
            status=LeaveStatus.PENDING,
        )

        available = calculator.calculate_available_days(balance, [pending_request])
        assert available == Decimal("12")  # 15 - 3 = 12

    def test_calculate_available_ignores_different_leave_type(self):
        """Test that pending requests of different leave type are ignored."""
        calculator = LeaveBalanceCalculator()

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

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 17),
        )
        pending_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=2,  # Different leave type
            period=period,
            status=LeaveStatus.PENDING,
        )

        available = calculator.calculate_available_days(balance, [pending_request])
        assert available == Decimal("15")  # Not affected

    def test_calculate_available_never_negative(self):
        """Test that available days is never negative."""
        calculator = LeaveBalanceCalculator()

        entitlement = LeaveEntitlement(
            entitled_days=Decimal("5"),
            used_days=Decimal("3"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 24),  # 10 days
        )
        pending_request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
            status=LeaveStatus.PENDING,
        )

        available = calculator.calculate_available_days(balance, [pending_request])
        assert available == Decimal("0")

    def test_can_request_with_sufficient_balance(self):
        """Test can_request returns true with sufficient balance."""
        calculator = LeaveBalanceCalculator()

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

        assert calculator.can_request(balance, 10, []) is True

    def test_can_request_with_insufficient_balance(self):
        """Test can_request returns false with insufficient balance."""
        calculator = LeaveBalanceCalculator()

        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("15"),
        )
        balance = LeaveBalance(
            id=1,
            employee_id=100,
            leave_type_id=1,
            year=2024,
            entitlement=entitlement,
        )

        assert calculator.can_request(balance, 10, []) is False


class TestDefaultLeaveApprovalPolicy:
    """Tests for DefaultLeaveApprovalPolicy service."""

    def test_can_approve_pending_request(self):
        """Test can approve pending request."""
        policy = DefaultLeaveApprovalPolicy()

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

        can_approve, reason = policy.can_approve(request, reviewer_id=200)
        assert can_approve is True
        assert reason is None

    def test_cannot_approve_already_approved(self):
        """Test cannot approve already approved request."""
        policy = DefaultLeaveApprovalPolicy()

        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        request = LeaveRequest(
            id=1,
            employee_id=100,
            leave_type_id=1,
            period=period,
            status=LeaveStatus.APPROVED,
        )

        can_approve, reason = policy.can_approve(request, reviewer_id=200)
        assert can_approve is False
        assert reason is not None

    def test_cannot_self_approve(self):
        """Test cannot self-approve own request."""
        policy = DefaultLeaveApprovalPolicy()

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

        can_approve, reason = policy.can_approve(request, reviewer_id=100)  # Same employee
        assert can_approve is False
        assert "self-approve" in reason.lower()


class TestDefaultLeaveYearService:
    """Tests for DefaultLeaveYearService."""

    def test_get_current_year(self):
        """Test getting current leave year."""
        service = DefaultLeaveYearService()
        current_year = service.get_current_year()
        assert current_year == date.today().year

    def test_get_year_start(self):
        """Test getting year start date."""
        service = DefaultLeaveYearService()
        year_start = service.get_year_start(2024)
        assert year_start == date(2024, 1, 1)

    def test_get_year_end(self):
        """Test getting year end date."""
        service = DefaultLeaveYearService()
        year_end = service.get_year_end(2024)
        assert year_end == date(2024, 12, 31)

    def test_is_within_leave_year(self):
        """Test checking if date is within leave year."""
        service = DefaultLeaveYearService()
        assert service.is_within_leave_year(date(2024, 6, 15), 2024) is True
        assert service.is_within_leave_year(date(2023, 12, 31), 2024) is False
        assert service.is_within_leave_year(date(2025, 1, 1), 2024) is False

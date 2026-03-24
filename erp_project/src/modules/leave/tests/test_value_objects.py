"""
Tests for leave value objects.
"""

from datetime import date
from decimal import Decimal

import pytest

from modules.leave.domain.value_objects import (
    LeaveEntitlement,
    LeavePeriod,
    LeaveStatus,
)


class TestLeaveStatus:
    """Tests for LeaveStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert LeaveStatus.PENDING.value == "Pending"
        assert LeaveStatus.APPROVED.value == "Approved"
        assert LeaveStatus.REJECTED.value == "Rejected"
        assert LeaveStatus.CANCELLED.value == "Cancelled"

    def test_status_string_representation(self):
        """Test string representation."""
        assert str(LeaveStatus.PENDING) == "LeaveStatus.PENDING"


class TestLeavePeriod:
    """Tests for LeavePeriod value object."""

    def test_create_valid_period(self):
        """Test creating a valid leave period."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert period.start_date == date(2024, 1, 15)
        assert period.end_date == date(2024, 1, 19)

    def test_days_calculation(self):
        """Test days calculation."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        # 15, 16, 17, 18, 19 = 5 days
        assert period.days == 5

    def test_single_day_period(self):
        """Test single day period."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 15),
        )
        assert period.days == 1

    def test_overlaps_with_overlapping_period(self):
        """Test overlap detection with overlapping periods."""
        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 18),
            end_date=date(2024, 1, 22),
        )
        assert period1.overlaps_with(period2) is True
        assert period2.overlaps_with(period1) is True

    def test_overlaps_with_non_overlapping_period(self):
        """Test overlap detection with non-overlapping periods."""
        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 22),
            end_date=date(2024, 1, 25),
        )
        assert period1.overlaps_with(period2) is False
        assert period2.overlaps_with(period1) is False

    def test_overlaps_with_adjacent_period(self):
        """Test overlap detection with adjacent periods (no overlap)."""
        period1 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 20),
            end_date=date(2024, 1, 25),
        )
        assert period1.overlaps_with(period2) is False

    def test_overlaps_with_contained_period(self):
        """Test overlap detection with contained period."""
        period1 = LeavePeriod(
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 25),
        )
        period2 = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert period1.overlaps_with(period2) is True
        assert period2.overlaps_with(period1) is True

    def test_contains_date_within_period(self):
        """Test if period contains a date within its range."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert period.contains(date(2024, 1, 17)) is True

    def test_contains_date_on_boundaries(self):
        """Test if period contains dates on boundaries."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert period.contains(date(2024, 1, 15)) is True
        assert period.contains(date(2024, 1, 19)) is True

    def test_contains_date_outside_period(self):
        """Test if period contains a date outside its range."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        assert period.contains(date(2024, 1, 14)) is False
        assert period.contains(date(2024, 1, 20)) is False

    def test_invalid_period_start_after_end(self):
        """Test that invalid period raises error."""
        with pytest.raises(ValueError):
            LeavePeriod(
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 15),
            )

    def test_period_immutability(self):
        """Test that period is immutable."""
        period = LeavePeriod(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19),
        )
        with pytest.raises(AttributeError):
            period.start_date = date(2024, 1, 10)


class TestLeaveEntitlement:
    """Tests for LeaveEntitlement value object."""

    def test_create_valid_entitlement(self):
        """Test creating a valid entitlement."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        assert entitlement.entitled_days == Decimal("20")
        assert entitlement.used_days == Decimal("5")

    def test_remaining_days_calculation(self):
        """Test remaining days calculation."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        assert entitlement.remaining_days == Decimal("15")

    def test_usage_percentage_calculation(self):
        """Test usage percentage calculation."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("10"),
        )
        assert entitlement.usage_percentage == Decimal("50.00")

    def test_usage_percentage_with_zero_entitled(self):
        """Test usage percentage when entitled is zero."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("0"),
            used_days=Decimal("0"),
        )
        assert entitlement.usage_percentage == Decimal("0")

    def test_is_exhausted_when_no_remaining(self):
        """Test is_exhausted when no days remaining."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("20"),
        )
        assert entitlement.is_exhausted is True

    def test_is_exhausted_when_days_remaining(self):
        """Test is_exhausted when days remaining."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("10"),
        )
        assert entitlement.is_exhausted is False

    def test_with_usage(self):
        """Test adding usage days."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        new_entitlement = entitlement.with_usage(Decimal("3"))
        assert new_entitlement.used_days == Decimal("8")
        assert entitlement.used_days == Decimal("5")  # Original unchanged

    def test_with_reversal(self):
        """Test reversing usage days."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("10"),
        )
        new_entitlement = entitlement.with_reversal(Decimal("3"))
        assert new_entitlement.used_days == Decimal("7")

    def test_with_adjusted_entitlement(self):
        """Test adjusting entitled days."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        new_entitlement = entitlement.with_adjusted_entitlement(Decimal("25"))
        assert new_entitlement.entitled_days == Decimal("25")
        assert new_entitlement.used_days == Decimal("5")

    def test_negative_entitled_days_raises_error(self):
        """Test that negative entitled days raises error."""
        with pytest.raises(ValueError):
            LeaveEntitlement(
                entitled_days=Decimal("-5"),
                used_days=Decimal("0"),
            )

    def test_negative_used_days_raises_error(self):
        """Test that negative used days raises error."""
        with pytest.raises(ValueError):
            LeaveEntitlement(
                entitled_days=Decimal("20"),
                used_days=Decimal("-5"),
            )

    def test_used_exceeds_entitled_raises_error(self):
        """Test that used exceeding entitled raises error."""
        with pytest.raises(ValueError):
            LeaveEntitlement(
                entitled_days=Decimal("20"),
                used_days=Decimal("25"),
            )

    def test_entitlement_immutability(self):
        """Test that entitlement is immutable."""
        entitlement = LeaveEntitlement(
            entitled_days=Decimal("20"),
            used_days=Decimal("5"),
        )
        with pytest.raises(AttributeError):
            entitlement.entitled_days = Decimal("25")

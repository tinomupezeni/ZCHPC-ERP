"""
Tests for recruitment value objects.
"""

from decimal import Decimal

import pytest

from modules.recruitment.domain.value_objects import (
    ApplicationStatus,
    JobStatus,
    SalaryRange,
)


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert JobStatus.DRAFT.value == "Draft"
        assert JobStatus.OPEN.value == "Open"
        assert JobStatus.CLOSED.value == "Closed"
        assert JobStatus.PENDING.value == "Pending"

    def test_from_string(self):
        """Test creating status from string."""
        assert JobStatus.from_string("Open") == JobStatus.OPEN
        assert JobStatus.from_string("open") == JobStatus.OPEN
        assert JobStatus.from_string("OPEN") == JobStatus.OPEN

    def test_from_string_invalid(self):
        """Test creating status from invalid string."""
        with pytest.raises(ValueError):
            JobStatus.from_string("Invalid")


class TestApplicationStatus:
    """Tests for ApplicationStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert ApplicationStatus.PENDING.value == "Pending"
        assert ApplicationStatus.SHORTLISTED.value == "Shortlisted"
        assert ApplicationStatus.INTERVIEW.value == "Interview"
        assert ApplicationStatus.OFFERED.value == "Offered"
        assert ApplicationStatus.HIRED.value == "Hired"
        assert ApplicationStatus.REJECTED.value == "Rejected"

    def test_is_final_hired(self):
        """Test is_final for hired status."""
        assert ApplicationStatus.HIRED.is_final is True

    def test_is_final_rejected(self):
        """Test is_final for rejected status."""
        assert ApplicationStatus.REJECTED.is_final is True

    def test_is_final_pending(self):
        """Test is_final for pending status."""
        assert ApplicationStatus.PENDING.is_final is False

    def test_is_active_pending(self):
        """Test is_active for pending status."""
        assert ApplicationStatus.PENDING.is_active is True

    def test_is_active_hired(self):
        """Test is_active for hired status."""
        assert ApplicationStatus.HIRED.is_active is False


class TestSalaryRange:
    """Tests for SalaryRange value object."""

    def test_create_usd_range(self):
        """Test creating a USD salary range."""
        salary = SalaryRange(
            usd_min=Decimal("50000"),
            usd_max=Decimal("70000"),
        )
        assert salary.usd_min == Decimal("50000")
        assert salary.usd_max == Decimal("70000")
        assert salary.has_usd_range is True
        assert salary.has_zig_range is False

    def test_create_zig_range(self):
        """Test creating a ZIG salary range."""
        salary = SalaryRange(
            zig_min=Decimal("500000"),
            zig_max=Decimal("700000"),
        )
        assert salary.zig_min == Decimal("500000")
        assert salary.zig_max == Decimal("700000")
        assert salary.has_zig_range is True
        assert salary.has_usd_range is False

    def test_create_dual_currency_range(self):
        """Test creating a dual currency salary range."""
        salary = SalaryRange(
            usd_min=Decimal("50000"),
            usd_max=Decimal("70000"),
            zig_min=Decimal("500000"),
            zig_max=Decimal("700000"),
        )
        assert salary.has_usd_range is True
        assert salary.has_zig_range is True

    def test_empty_range(self):
        """Test creating an empty salary range."""
        salary = SalaryRange.empty()
        assert salary.usd_min is None
        assert salary.usd_max is None
        assert salary.zig_min is None
        assert salary.zig_max is None

    def test_usd_display_full_range(self):
        """Test USD display for full range."""
        salary = SalaryRange(
            usd_min=Decimal("50000"),
            usd_max=Decimal("70000"),
        )
        assert "$50,000.00 - $70,000.00" in salary.usd_display

    def test_usd_display_min_only(self):
        """Test USD display for minimum only."""
        salary = SalaryRange(usd_min=Decimal("50000"))
        assert "From $50,000.00" in salary.usd_display

    def test_usd_display_max_only(self):
        """Test USD display for maximum only."""
        salary = SalaryRange(usd_max=Decimal("70000"))
        assert "Up to $70,000.00" in salary.usd_display

    def test_invalid_usd_min_greater_than_max(self):
        """Test that min > max raises error."""
        with pytest.raises(ValueError):
            SalaryRange(
                usd_min=Decimal("80000"),
                usd_max=Decimal("70000"),
            )

    def test_invalid_negative_salary(self):
        """Test that negative salary raises error."""
        with pytest.raises(ValueError):
            SalaryRange(
                usd_min=Decimal("-1000"),
                usd_max=Decimal("70000"),
            )

    def test_immutability(self):
        """Test that salary range is immutable."""
        salary = SalaryRange(
            usd_min=Decimal("50000"),
            usd_max=Decimal("70000"),
        )
        with pytest.raises(AttributeError):
            salary.usd_min = Decimal("60000")

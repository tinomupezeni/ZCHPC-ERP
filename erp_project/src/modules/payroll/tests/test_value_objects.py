"""
Tests for payroll value objects.
"""

from decimal import Decimal

import pytest

from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    PayrollStatus,
    PayslipStatus,
    TaxBracket,
    Currency,
    Earnings,
    Deductions,
)


class TestPayrollPeriod:
    """Tests for PayrollPeriod value object."""

    def test_create_period(self):
        """Test creating a period."""
        period = PayrollPeriod(year=2025, month=3)
        assert period.year == 2025
        assert period.month == 3

    def test_period_display(self):
        """Test display format."""
        period = PayrollPeriod(year=2025, month=3)
        assert period.display == "March 2025"

    def test_period_code(self):
        """Test code format."""
        period = PayrollPeriod(year=2025, month=3)
        assert period.code == "2025-03"

    def test_from_string(self):
        """Test creating from string."""
        period = PayrollPeriod.from_string("2025-03")
        assert period.year == 2025
        assert period.month == 3

    def test_next_period(self):
        """Test getting next period."""
        period = PayrollPeriod(year=2025, month=3)
        next_p = period.next()
        assert next_p.year == 2025
        assert next_p.month == 4

    def test_next_period_year_rollover(self):
        """Test next period with year rollover."""
        period = PayrollPeriod(year=2025, month=12)
        next_p = period.next()
        assert next_p.year == 2026
        assert next_p.month == 1

    def test_previous_period(self):
        """Test getting previous period."""
        period = PayrollPeriod(year=2025, month=3)
        prev_p = period.previous()
        assert prev_p.year == 2025
        assert prev_p.month == 2

    def test_previous_period_year_rollover(self):
        """Test previous period with year rollover."""
        period = PayrollPeriod(year=2025, month=1)
        prev_p = period.previous()
        assert prev_p.year == 2024
        assert prev_p.month == 12

    def test_invalid_month(self):
        """Test invalid month raises error."""
        with pytest.raises(ValueError):
            PayrollPeriod(year=2025, month=13)

    def test_invalid_year(self):
        """Test invalid year raises error."""
        with pytest.raises(ValueError):
            PayrollPeriod(year=1800, month=3)


class TestPayrollStatus:
    """Tests for PayrollStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert PayrollStatus.OPEN.value == "Open"
        assert PayrollStatus.PROCESSING.value == "Processing"
        assert PayrollStatus.CLOSED.value == "Closed"

    def test_can_process(self):
        """Test can_process property."""
        assert PayrollStatus.OPEN.can_process is True
        assert PayrollStatus.PROCESSING.can_process is False
        assert PayrollStatus.CLOSED.can_process is False

    def test_can_reopen(self):
        """Test can_reopen property."""
        assert PayrollStatus.CLOSED.can_reopen is True
        assert PayrollStatus.OPEN.can_reopen is False


class TestPayslipStatus:
    """Tests for PayslipStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert PayslipStatus.DRAFT.value == "Draft"
        assert PayslipStatus.PROCESSED.value == "Processed"
        assert PayslipStatus.PAID.value == "Paid"

    def test_is_final(self):
        """Test is_final property."""
        assert PayslipStatus.DRAFT.is_final is False
        assert PayslipStatus.PROCESSED.is_final is True
        assert PayslipStatus.PAID.is_final is True

    def test_can_edit(self):
        """Test can_edit property."""
        assert PayslipStatus.DRAFT.can_edit is True
        assert PayslipStatus.PROCESSED.can_edit is False


class TestTaxBracket:
    """Tests for TaxBracket value object."""

    def test_create_bracket(self):
        """Test creating a tax bracket."""
        bracket = TaxBracket(
            min_income=Decimal("1000"),
            max_income=Decimal("2000"),
            rate=Decimal("0.20"),
            deduction=Decimal("100"),
            currency=Currency.USD
        )
        assert bracket.min_income == Decimal("1000")
        assert bracket.rate == Decimal("0.20")

    def test_applies_to(self):
        """Test applies_to method."""
        bracket = TaxBracket(
            min_income=Decimal("1000"),
            max_income=Decimal("2000"),
            rate=Decimal("0.20"),
            deduction=Decimal("100"),
            currency=Currency.USD
        )
        assert bracket.applies_to(Decimal("1500")) is True
        assert bracket.applies_to(Decimal("500")) is False
        assert bracket.applies_to(Decimal("2500")) is False

    def test_calculate_tax(self):
        """Test tax calculation."""
        bracket = TaxBracket(
            min_income=Decimal("1000"),
            max_income=Decimal("2000"),
            rate=Decimal("0.20"),
            deduction=Decimal("100"),
            currency=Currency.USD
        )
        # (1500 * 0.20) - 100 = 300 - 100 = 200
        tax = bracket.calculate_tax(Decimal("1500"))
        assert tax == Decimal("200")

    def test_negative_tax_returns_zero(self):
        """Test that negative tax returns zero."""
        bracket = TaxBracket(
            min_income=Decimal("0"),
            max_income=Decimal("1000"),
            rate=Decimal("0.05"),
            deduction=Decimal("100"),
            currency=Currency.USD
        )
        # (500 * 0.05) - 100 = 25 - 100 = -75 → 0
        tax = bracket.calculate_tax(Decimal("500"))
        assert tax == Decimal("0")

    def test_invalid_rate(self):
        """Test invalid rate raises error."""
        with pytest.raises(ValueError):
            TaxBracket(
                min_income=Decimal("1000"),
                max_income=Decimal("2000"),
                rate=Decimal("1.5"),  # > 1
                deduction=Decimal("100"),
                currency=Currency.USD
            )


class TestCurrency:
    """Tests for Currency enum."""

    def test_from_string(self):
        """Test from_string method."""
        assert Currency.from_string("USD") == Currency.USD
        assert Currency.from_string("usd") == Currency.USD
        assert Currency.from_string("ZIG") == Currency.ZIG

    def test_invalid_currency(self):
        """Test invalid currency raises error."""
        with pytest.raises(ValueError):
            Currency.from_string("EUR")


class TestEarnings:
    """Tests for Earnings value object."""

    def test_create_earnings(self):
        """Test creating earnings."""
        earnings = Earnings(
            base_salary_usd=Decimal("5000"),
            base_salary_zig=Decimal("50000")
        )
        assert earnings.base_salary_usd == Decimal("5000")
        assert earnings.gross_usd == Decimal("5000")

    def test_with_allowance(self):
        """Test adding an allowance."""
        earnings = Earnings(
            base_salary_usd=Decimal("5000"),
            base_salary_zig=Decimal("50000")
        )
        new_earnings = earnings.with_allowance(
            "Housing", amount_usd=Decimal("500")
        )
        assert new_earnings.total_allowances_usd == Decimal("500")
        assert new_earnings.gross_usd == Decimal("5500")


class TestDeductions:
    """Tests for Deductions value object."""

    def test_create_statutory(self):
        """Test creating statutory deductions."""
        deductions = Deductions.create_statutory(
            paye_usd=Decimal("500"),
            paye_zig=Decimal("5000"),
            aids_levy_usd=Decimal("15"),
            aids_levy_zig=Decimal("150"),
            nssa_employee_usd=Decimal("225"),
            nssa_employee_zig=Decimal("2250"),
            nssa_employer_usd=Decimal("225"),
            nssa_employer_zig=Decimal("2250")
        )
        assert deductions.paye_usd == Decimal("500")
        assert deductions.total_statutory_usd == Decimal("740")

    def test_total_excludes_employer_contributions(self):
        """Test that total excludes employer contributions."""
        deductions = Deductions.create_statutory(
            paye_usd=Decimal("500"),
            paye_zig=Decimal("0"),
            aids_levy_usd=Decimal("15"),
            aids_levy_zig=Decimal("0"),
            nssa_employee_usd=Decimal("225"),
            nssa_employee_zig=Decimal("0"),
            nssa_employer_usd=Decimal("225"),
            nssa_employer_zig=Decimal("0")
        )
        # Total should be 500 + 15 + 225 = 740 (excludes employer 225)
        assert deductions.total_usd == Decimal("740")
        assert deductions.total_employer_usd == Decimal("225")

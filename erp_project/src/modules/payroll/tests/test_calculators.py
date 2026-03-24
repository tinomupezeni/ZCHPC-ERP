"""
Tests for payroll calculators.
"""

from decimal import Decimal

import pytest

from modules.payroll.domain.value_objects import Currency, TaxBracket
from modules.payroll.domain.entities import TaxTable
from modules.payroll.domain.services import (
    TaxCalculator,
    AIDSLevyCalculator,
    NSSACalculator,
)


class TestTaxCalculator:
    """Tests for TaxCalculator."""

    @pytest.fixture
    def tax_table(self):
        """Create a sample tax table."""
        brackets = [
            TaxBracket(
                min_income=Decimal("0"),
                max_income=Decimal("300"),
                rate=Decimal("0"),
                deduction=Decimal("0"),
                currency=Currency.USD
            ),
            TaxBracket(
                min_income=Decimal("300"),
                max_income=Decimal("1000"),
                rate=Decimal("0.10"),
                deduction=Decimal("30"),
                currency=Currency.USD
            ),
            TaxBracket(
                min_income=Decimal("1000"),
                max_income=Decimal("2000"),
                rate=Decimal("0.15"),
                deduction=Decimal("80"),
                currency=Currency.USD
            ),
            TaxBracket(
                min_income=Decimal("2000"),
                max_income=None,
                rate=Decimal("0.20"),
                deduction=Decimal("180"),
                currency=Currency.USD
            ),
        ]
        return TaxTable(
            id=1,
            currency=Currency.USD,
            effective_from=None,
            brackets=brackets
        )

    def test_zero_income(self, tax_table):
        """Test zero income has zero tax."""
        tax = TaxCalculator.calculate_paye(Decimal("0"), tax_table)
        assert tax == Decimal("0")

    def test_first_bracket_no_tax(self, tax_table):
        """Test income in first bracket (0% tax)."""
        tax = TaxCalculator.calculate_paye(Decimal("200"), tax_table)
        assert tax == Decimal("0")

    def test_second_bracket(self, tax_table):
        """Test income in second bracket."""
        # (500 * 0.10) - 30 = 50 - 30 = 20
        tax = TaxCalculator.calculate_paye(Decimal("500"), tax_table)
        assert tax == Decimal("20")

    def test_third_bracket(self, tax_table):
        """Test income in third bracket."""
        # (1500 * 0.15) - 80 = 225 - 80 = 145
        tax = TaxCalculator.calculate_paye(Decimal("1500"), tax_table)
        assert tax == Decimal("145")

    def test_highest_bracket(self, tax_table):
        """Test income in highest bracket."""
        # (3000 * 0.20) - 180 = 600 - 180 = 420
        tax = TaxCalculator.calculate_paye(Decimal("3000"), tax_table)
        assert tax == Decimal("420")

    def test_from_brackets_tuples(self):
        """Test calculation from raw bracket tuples."""
        brackets = [
            (Decimal("0"), Decimal("300"), Decimal("0"), Decimal("0")),
            (Decimal("300"), Decimal("1000"), Decimal("0.10"), Decimal("30")),
            (Decimal("1000"), None, Decimal("0.15"), Decimal("80")),
        ]
        tax = TaxCalculator.calculate_paye_from_brackets(
            Decimal("1500"), brackets
        )
        # (1500 * 0.15) - 80 = 225 - 80 = 145
        assert tax == Decimal("145")


class TestAIDSLevyCalculator:
    """Tests for AIDSLevyCalculator."""

    def test_calculate_levy(self):
        """Test AIDS levy calculation."""
        # 3% of PAYE
        levy = AIDSLevyCalculator.calculate(Decimal("1000"))
        assert levy == Decimal("30")

    def test_zero_paye(self):
        """Test zero PAYE results in zero levy."""
        levy = AIDSLevyCalculator.calculate(Decimal("0"))
        assert levy == Decimal("0")

    def test_not_paying_levy(self):
        """Test when employee doesn't pay levy."""
        levy = AIDSLevyCalculator.calculate(Decimal("1000"), pays_levy=False)
        assert levy == Decimal("0")


class TestNSSACalculator:
    """Tests for NSSACalculator."""

    def test_calculate_both_contributions(self):
        """Test calculating both employee and employer contributions."""
        employee, employer = NSSACalculator.calculate(Decimal("10000"))
        # 4.5% each
        assert employee == Decimal("450")
        assert employer == Decimal("450")

    def test_calculate_employee_only(self):
        """Test calculating employee contribution only."""
        employee = NSSACalculator.calculate_employee(Decimal("10000"))
        assert employee == Decimal("450")

    def test_calculate_employer_only(self):
        """Test calculating employer contribution only."""
        employer = NSSACalculator.calculate_employer(Decimal("10000"))
        assert employer == Decimal("450")

    def test_zero_salary(self):
        """Test zero salary results in zero contributions."""
        employee, employer = NSSACalculator.calculate(Decimal("0"))
        assert employee == Decimal("0")
        assert employer == Decimal("0")

    def test_negative_salary(self):
        """Test negative salary results in zero contributions."""
        employee, employer = NSSACalculator.calculate(Decimal("-1000"))
        assert employee == Decimal("0")
        assert employer == Decimal("0")

    def test_decimal_precision(self):
        """Test that results are properly quantized."""
        employee, employer = NSSACalculator.calculate(Decimal("1234.56"))
        # 1234.56 * 0.045 = 55.5552 → 55.56
        assert employee == Decimal("55.56")
        assert employer == Decimal("55.56")

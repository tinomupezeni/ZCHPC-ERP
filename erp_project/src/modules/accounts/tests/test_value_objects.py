"""
Tests for accounts domain value objects.
"""

import pytest
from decimal import Decimal

from modules.accounts.domain.value_objects import (
    AccountType,
    JournalType,
    PartnerType,
    AccountCode,
    Money,
    DebitCredit,
)


class TestAccountType:
    """Tests for AccountType enum."""

    def test_asset_is_posting(self):
        assert AccountType.ASSET.is_posting is True

    def test_liability_is_posting(self):
        assert AccountType.LIABILITY.is_posting is True

    def test_view_is_not_posting(self):
        assert AccountType.VIEW.is_posting is False

    def test_asset_normal_balance_is_debit(self):
        assert AccountType.ASSET.normal_balance == "debit"

    def test_liability_normal_balance_is_credit(self):
        assert AccountType.LIABILITY.normal_balance == "credit"

    def test_revenue_normal_balance_is_credit(self):
        assert AccountType.REVENUE.normal_balance == "credit"

    def test_expense_normal_balance_is_debit(self):
        assert AccountType.EXPENSE.normal_balance == "debit"


class TestAccountCode:
    """Tests for AccountCode value object."""

    def test_create_valid_code(self):
        code = AccountCode(value="1000")
        assert code.value == "1000"

    def test_is_asset_code(self):
        code = AccountCode(value="1000")
        assert code.is_asset is True
        assert code.is_liability is False

    def test_is_liability_code(self):
        code = AccountCode(value="2000")
        assert code.is_liability is True
        assert code.is_asset is False

    def test_is_equity_code(self):
        code = AccountCode(value="3000")
        assert code.is_equity is True

    def test_is_revenue_code(self):
        code = AccountCode(value="4000")
        assert code.is_revenue is True

    def test_is_expense_code(self):
        code = AccountCode(value="5000")
        assert code.is_expense is True

    def test_codes_equal(self):
        code1 = AccountCode(value="1000")
        code2 = AccountCode(value="1000")
        assert code1 == code2

    def test_codes_not_equal(self):
        code1 = AccountCode(value="1000")
        code2 = AccountCode(value="2000")
        assert code1 != code2


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self):
        money = Money(amount=Decimal("100.00"), currency_code="USD")
        assert money.amount == Decimal("100.00")
        assert money.currency_code == "USD"

    def test_add_same_currency(self):
        m1 = Money(amount=Decimal("100.00"), currency_code="USD")
        m2 = Money(amount=Decimal("50.00"), currency_code="USD")
        result = m1 + m2
        assert result.amount == Decimal("150.00")

    def test_add_different_currency_raises(self):
        m1 = Money(amount=Decimal("100.00"), currency_code="USD")
        m2 = Money(amount=Decimal("50.00"), currency_code="EUR")
        with pytest.raises(ValueError):
            m1 + m2

    def test_subtract_same_currency(self):
        m1 = Money(amount=Decimal("100.00"), currency_code="USD")
        m2 = Money(amount=Decimal("30.00"), currency_code="USD")
        result = m1 - m2
        assert result.amount == Decimal("70.00")

    def test_multiply_by_scalar(self):
        money = Money(amount=Decimal("100.00"), currency_code="USD")
        result = money * 2
        assert result.amount == Decimal("200.00")

    def test_negate(self):
        money = Money(amount=Decimal("100.00"), currency_code="USD")
        result = -money
        assert result.amount == Decimal("-100.00")

    def test_is_positive(self):
        money = Money(amount=Decimal("100.00"), currency_code="USD")
        assert money.is_positive is True
        assert money.is_negative is False

    def test_is_negative(self):
        money = Money(amount=Decimal("-100.00"), currency_code="USD")
        assert money.is_negative is True
        assert money.is_positive is False

    def test_is_zero(self):
        money = Money(amount=Decimal("0.00"), currency_code="USD")
        assert money.is_zero is True


class TestDebitCredit:
    """Tests for DebitCredit value object."""

    def test_create_debit(self):
        dc = DebitCredit(debit=Decimal("100.00"))
        assert dc.debit == Decimal("100.00")
        assert dc.credit == Decimal("0")

    def test_create_credit(self):
        dc = DebitCredit(credit=Decimal("100.00"))
        assert dc.debit == Decimal("0")
        assert dc.credit == Decimal("100.00")

    def test_balance_with_debit(self):
        dc = DebitCredit(debit=Decimal("100.00"))
        assert dc.balance == Decimal("100.00")

    def test_balance_with_credit(self):
        dc = DebitCredit(credit=Decimal("100.00"))
        assert dc.balance == Decimal("-100.00")

    def test_is_debit(self):
        dc = DebitCredit(debit=Decimal("100.00"))
        assert dc.is_debit is True
        assert dc.is_credit is False

    def test_is_credit(self):
        dc = DebitCredit(credit=Decimal("100.00"))
        assert dc.is_credit is True
        assert dc.is_debit is False

    def test_is_balanced_with_zeros(self):
        dc = DebitCredit()
        assert dc.is_balanced is True

    def test_add_debit_credits(self):
        dc1 = DebitCredit(debit=Decimal("100.00"))
        dc2 = DebitCredit(credit=Decimal("50.00"))
        result = dc1 + dc2
        assert result.debit == Decimal("100.00")
        assert result.credit == Decimal("50.00")
        assert result.balance == Decimal("50.00")


class TestJournalType:
    """Tests for JournalType enum."""

    def test_journal_types_exist(self):
        assert JournalType.SALE.value == "Sale"
        assert JournalType.PURCHASE.value == "Purchase"
        assert JournalType.CASH.value == "Cash"
        assert JournalType.BANK.value == "Bank"
        assert JournalType.GENERAL.value == "General"


class TestPartnerType:
    """Tests for PartnerType enum."""

    def test_partner_types_exist(self):
        assert PartnerType.CUSTOMER.value == "Customer"
        assert PartnerType.SUPPLIER.value == "Supplier"
        assert PartnerType.EMPLOYEE.value == "Employee"

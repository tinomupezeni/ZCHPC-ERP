"""
Tests for accounts domain services.
"""

import pytest
from datetime import date
from decimal import Decimal
from typing import List, Optional

from modules.accounts.domain.value_objects import AccountType
from modules.accounts.domain.services import (
    BalanceCalculator,
    AccountBalance,
    TrialBalanceGenerator,
    ProfitLossGenerator,
    BalanceSheetGenerator,
)


class MockLineReader:
    """Mock implementation of JournalEntryLineReader."""

    def __init__(self):
        self.lines = []

    def add_line(
        self,
        account_id: int,
        debit: Decimal = Decimal("0"),
        credit: Decimal = Decimal("0"),
        partner_id: Optional[int] = None,
        entry_date: Optional[date] = None
    ):
        self.lines.append({
            "account_id": account_id,
            "debit": debit,
            "credit": credit,
            "partner_id": partner_id,
            "entry_date": entry_date or date.today()
        })

    def get_posted_lines_for_account(
        self,
        account_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        return [
            line for line in self.lines
            if line["account_id"] == account_id
            and (from_date is None or line["entry_date"] >= from_date)
            and (to_date is None or line["entry_date"] <= to_date)
        ]

    def get_posted_lines_for_accounts(
        self,
        account_ids: List[int],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        return [
            line for line in self.lines
            if line["account_id"] in account_ids
            and (from_date is None or line["entry_date"] >= from_date)
            and (to_date is None or line["entry_date"] <= to_date)
        ]


class TestBalanceCalculator:
    """Tests for BalanceCalculator service."""

    def test_calculate_debit_balance(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("100.00"))
        reader.add_line(account_id=1, debit=Decimal("50.00"))

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_balance(
            account_id=1,
            account_code="1000",
            account_name="Cash",
            account_type=AccountType.ASSET
        )

        assert balance.debit_total == Decimal("150.00")
        assert balance.credit_total == Decimal("0")
        assert balance.balance == Decimal("150.00")

    def test_calculate_credit_balance(self):
        reader = MockLineReader()
        reader.add_line(account_id=2, credit=Decimal("200.00"))
        reader.add_line(account_id=2, credit=Decimal("100.00"))

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_balance(
            account_id=2,
            account_code="4000",
            account_name="Revenue",
            account_type=AccountType.REVENUE
        )

        assert balance.debit_total == Decimal("0")
        assert balance.credit_total == Decimal("300.00")
        assert balance.balance == Decimal("-300.00")

    def test_calculate_mixed_balance(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("500.00"))
        reader.add_line(account_id=1, credit=Decimal("200.00"))

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_balance(
            account_id=1,
            account_code="1000",
            account_name="Cash",
            account_type=AccountType.ASSET
        )

        assert balance.debit_total == Decimal("500.00")
        assert balance.credit_total == Decimal("200.00")
        assert balance.balance == Decimal("300.00")

    def test_calculate_balances_multiple_accounts(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("100.00"))
        reader.add_line(account_id=2, credit=Decimal("100.00"))

        calculator = BalanceCalculator(reader)
        accounts = [
            {"id": 1, "code": "1000", "name": "Cash", "account_type": AccountType.ASSET},
            {"id": 2, "code": "4000", "name": "Revenue", "account_type": AccountType.REVENUE},
        ]

        balances = calculator.calculate_balances(accounts)

        assert len(balances) == 2
        assert balances[0].balance == Decimal("100.00")
        assert balances[1].balance == Decimal("-100.00")

    def test_calculate_partner_balance(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("500.00"), partner_id=10)
        reader.add_line(account_id=1, credit=Decimal("200.00"), partner_id=10)
        reader.add_line(account_id=1, debit=Decimal("300.00"), partner_id=20)

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_partner_balance(
            account_id=1,
            partner_id=10
        )

        assert balance == Decimal("300.00")

    def test_normal_balance_for_asset(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("100.00"))

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_balance(
            account_id=1,
            account_code="1000",
            account_name="Cash",
            account_type=AccountType.ASSET
        )

        # For assets, normal balance is debit - credit (positive when debit > credit)
        assert balance.normal_balance == Decimal("100.00")

    def test_normal_balance_for_liability(self):
        reader = MockLineReader()
        reader.add_line(account_id=2, credit=Decimal("100.00"))

        calculator = BalanceCalculator(reader)
        balance = calculator.calculate_balance(
            account_id=2,
            account_code="2000",
            account_name="Accounts Payable",
            account_type=AccountType.LIABILITY
        )

        # For liabilities, normal balance is credit - debit (positive when credit > debit)
        assert balance.normal_balance == Decimal("100.00")


class TestTrialBalanceGenerator:
    """Tests for TrialBalanceGenerator service."""

    def test_generate_trial_balance(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("1000.00"))
        reader.add_line(account_id=2, credit=Decimal("500.00"))
        reader.add_line(account_id=3, credit=Decimal("500.00"))

        calculator = BalanceCalculator(reader)
        generator = TrialBalanceGenerator(calculator)

        accounts = [
            {"id": 1, "code": "1000", "name": "Cash", "account_type": AccountType.ASSET},
            {"id": 2, "code": "2000", "name": "Payables", "account_type": AccountType.LIABILITY},
            {"id": 3, "code": "3000", "name": "Equity", "account_type": AccountType.EQUITY},
        ]

        trial_balance = generator.generate(
            accounts=accounts,
            as_of_date=date.today()
        )

        assert trial_balance.is_balanced is True
        assert trial_balance.total_debit == Decimal("1000.00")
        assert trial_balance.total_credit == Decimal("1000.00")
        assert len(trial_balance.items) == 3

    def test_trial_balance_excludes_zero_accounts(self):
        reader = MockLineReader()
        reader.add_line(account_id=1, debit=Decimal("100.00"))

        calculator = BalanceCalculator(reader)
        generator = TrialBalanceGenerator(calculator)

        accounts = [
            {"id": 1, "code": "1000", "name": "Cash", "account_type": AccountType.ASSET},
            {"id": 2, "code": "2000", "name": "Empty", "account_type": AccountType.LIABILITY},
        ]

        trial_balance = generator.generate(
            accounts=accounts,
            as_of_date=date.today()
        )

        # Account 2 has no entries, should be excluded
        assert len(trial_balance.items) == 1


class TestProfitLossGenerator:
    """Tests for ProfitLossGenerator service."""

    def test_generate_profit_loss(self):
        reader = MockLineReader()
        # Revenue
        reader.add_line(account_id=4, credit=Decimal("5000.00"))
        # Expense
        reader.add_line(account_id=5, debit=Decimal("3000.00"))

        calculator = BalanceCalculator(reader)
        generator = ProfitLossGenerator(calculator)

        accounts = [
            {"id": 4, "code": "4000", "name": "Sales", "account_type": AccountType.REVENUE},
            {"id": 5, "code": "5000", "name": "Wages", "account_type": AccountType.EXPENSE},
        ]

        pnl = generator.generate(
            accounts=accounts,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31)
        )

        assert pnl.total_revenue == Decimal("5000.00")
        assert pnl.total_expenses == Decimal("3000.00")
        assert pnl.net_income == Decimal("2000.00")
        assert pnl.is_profitable is True

    def test_generate_loss(self):
        reader = MockLineReader()
        reader.add_line(account_id=4, credit=Decimal("2000.00"))
        reader.add_line(account_id=5, debit=Decimal("5000.00"))

        calculator = BalanceCalculator(reader)
        generator = ProfitLossGenerator(calculator)

        accounts = [
            {"id": 4, "code": "4000", "name": "Sales", "account_type": AccountType.REVENUE},
            {"id": 5, "code": "5000", "name": "Expenses", "account_type": AccountType.EXPENSE},
        ]

        pnl = generator.generate(
            accounts=accounts,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 12, 31)
        )

        assert pnl.net_income == Decimal("-3000.00")
        assert pnl.is_profitable is False


class TestBalanceSheetGenerator:
    """Tests for BalanceSheetGenerator service."""

    def test_generate_balance_sheet(self):
        reader = MockLineReader()
        # Assets
        reader.add_line(account_id=1, debit=Decimal("10000.00"))
        # Liabilities
        reader.add_line(account_id=2, credit=Decimal("3000.00"))
        # Equity
        reader.add_line(account_id=3, credit=Decimal("7000.00"))

        calculator = BalanceCalculator(reader)
        pnl_generator = ProfitLossGenerator(calculator)
        generator = BalanceSheetGenerator(calculator, pnl_generator)

        accounts = [
            {"id": 1, "code": "1000", "name": "Cash", "account_type": AccountType.ASSET},
            {"id": 2, "code": "2000", "name": "Payables", "account_type": AccountType.LIABILITY},
            {"id": 3, "code": "3000", "name": "Capital", "account_type": AccountType.EQUITY},
        ]

        balance_sheet = generator.generate(
            accounts=accounts,
            as_of_date=date.today()
        )

        assert balance_sheet.total_assets == Decimal("10000.00")
        assert balance_sheet.total_liabilities == Decimal("3000.00")
        assert balance_sheet.total_equity == Decimal("7000.00")
        assert balance_sheet.is_balanced is True

    def test_balance_sheet_with_retained_earnings(self):
        reader = MockLineReader()
        # Assets
        reader.add_line(account_id=1, debit=Decimal("15000.00"))
        # Liabilities
        reader.add_line(account_id=2, credit=Decimal("3000.00"))
        # Equity
        reader.add_line(account_id=3, credit=Decimal("7000.00"))
        # Revenue
        reader.add_line(account_id=4, credit=Decimal("10000.00"))
        # Expense
        reader.add_line(account_id=5, debit=Decimal("5000.00"))

        calculator = BalanceCalculator(reader)
        pnl_generator = ProfitLossGenerator(calculator)
        generator = BalanceSheetGenerator(calculator, pnl_generator)

        accounts = [
            {"id": 1, "code": "1000", "name": "Cash", "account_type": AccountType.ASSET},
            {"id": 2, "code": "2000", "name": "Payables", "account_type": AccountType.LIABILITY},
            {"id": 3, "code": "3000", "name": "Capital", "account_type": AccountType.EQUITY},
            {"id": 4, "code": "4000", "name": "Revenue", "account_type": AccountType.REVENUE},
            {"id": 5, "code": "5000", "name": "Expenses", "account_type": AccountType.EXPENSE},
        ]

        balance_sheet = generator.generate(
            accounts=accounts,
            as_of_date=date.today(),
            fiscal_year_start=date(2024, 1, 1)
        )

        # Retained earnings = Revenue - Expenses = 10000 - 5000 = 5000
        assert balance_sheet.retained_earnings == Decimal("5000.00")
        # Total equity = Capital (7000) + Retained Earnings (5000) = 12000
        assert balance_sheet.total_equity == Decimal("12000.00")
        # Total assets (15000) = Total liabilities (3000) + Total equity (12000)
        assert balance_sheet.is_balanced is True

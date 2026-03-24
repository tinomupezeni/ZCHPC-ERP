"""
Financial report generation domain services.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from modules.accounts.domain.value_objects import AccountType
from modules.accounts.domain.services.balance_calculator import (
    AccountBalance,
    BalanceCalculator,
)


@dataclass
class TrialBalanceItem:
    """A single row in the trial balance."""

    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal


@dataclass
class TrialBalance:
    """Trial balance report data."""

    as_of_date: date
    items: List[TrialBalanceItem] = field(default_factory=list)

    @property
    def total_debit(self) -> Decimal:
        """Sum of all debit balances."""
        return sum((item.debit for item in self.items), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        """Sum of all credit balances."""
        return sum((item.credit for item in self.items), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        """Check if trial balance is balanced."""
        return self.total_debit == self.total_credit

    @property
    def difference(self) -> Decimal:
        """Get the difference (should be zero)."""
        return self.total_debit - self.total_credit


class TrialBalanceGenerator:
    """
    Domain service for generating trial balance reports.

    The trial balance lists all accounts with their debit/credit balances.
    """

    def __init__(self, balance_calculator: BalanceCalculator) -> None:
        self._balance_calculator = balance_calculator

    def generate(
        self,
        accounts: List[dict],
        as_of_date: date,
        from_date: Optional[date] = None
    ) -> TrialBalance:
        """
        Generate a trial balance report.

        Args:
            accounts: List of account dictionaries
            as_of_date: The date for the trial balance
            from_date: Optional start date for period

        Returns:
            TrialBalance report object
        """
        balances = self._balance_calculator.calculate_balances(
            accounts=accounts,
            from_date=from_date,
            to_date=as_of_date
        )

        items = []
        for balance in balances:
            # Only include accounts with activity
            if balance.debit_total == 0 and balance.credit_total == 0:
                continue

            # Display as debit or credit balance
            if balance.balance >= 0:
                debit = balance.balance
                credit = Decimal("0")
            else:
                debit = Decimal("0")
                credit = abs(balance.balance)

            items.append(TrialBalanceItem(
                account_code=balance.account_code,
                account_name=balance.account_name,
                debit=debit,
                credit=credit
            ))

        # Sort by account code
        items.sort(key=lambda x: x.account_code)

        return TrialBalance(as_of_date=as_of_date, items=items)


@dataclass
class ProfitLossSection:
    """A section in the P&L report."""

    title: str
    items: List[AccountBalance] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        """Total for this section."""
        return sum((item.normal_balance for item in self.items), Decimal("0"))


@dataclass
class ProfitLossReport:
    """Profit and Loss (Income Statement) report data."""

    from_date: date
    to_date: date
    revenue_section: ProfitLossSection = field(
        default_factory=lambda: ProfitLossSection(title="Revenue")
    )
    expense_section: ProfitLossSection = field(
        default_factory=lambda: ProfitLossSection(title="Expenses")
    )

    @property
    def total_revenue(self) -> Decimal:
        """Total revenue."""
        return self.revenue_section.total

    @property
    def total_expenses(self) -> Decimal:
        """Total expenses."""
        return self.expense_section.total

    @property
    def net_income(self) -> Decimal:
        """Net income (revenue - expenses)."""
        return self.total_revenue - self.total_expenses

    @property
    def is_profitable(self) -> bool:
        """Check if there is a net profit."""
        return self.net_income > 0


class ProfitLossGenerator:
    """
    Domain service for generating Profit & Loss reports.

    The P&L shows revenue and expenses for a period.
    """

    def __init__(self, balance_calculator: BalanceCalculator) -> None:
        self._balance_calculator = balance_calculator

    def generate(
        self,
        accounts: List[dict],
        from_date: date,
        to_date: date
    ) -> ProfitLossReport:
        """
        Generate a Profit & Loss report.

        Args:
            accounts: List of account dictionaries
            from_date: Period start date
            to_date: Period end date

        Returns:
            ProfitLossReport object
        """
        # Filter to only revenue and expense accounts
        revenue_accounts = [
            a for a in accounts
            if a.get("account_type") == AccountType.REVENUE.value
            or a.get("account_type") == AccountType.REVENUE
        ]
        expense_accounts = [
            a for a in accounts
            if a.get("account_type") == AccountType.EXPENSE.value
            or a.get("account_type") == AccountType.EXPENSE
        ]

        report = ProfitLossReport(from_date=from_date, to_date=to_date)

        # Calculate revenue balances
        if revenue_accounts:
            revenue_balances = self._balance_calculator.calculate_balances(
                accounts=revenue_accounts,
                from_date=from_date,
                to_date=to_date
            )
            report.revenue_section.items = [
                b for b in revenue_balances
                if b.debit_total != 0 or b.credit_total != 0
            ]

        # Calculate expense balances
        if expense_accounts:
            expense_balances = self._balance_calculator.calculate_balances(
                accounts=expense_accounts,
                from_date=from_date,
                to_date=to_date
            )
            report.expense_section.items = [
                b for b in expense_balances
                if b.debit_total != 0 or b.credit_total != 0
            ]

        return report


@dataclass
class BalanceSheetSection:
    """A section in the balance sheet."""

    title: str
    items: List[AccountBalance] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        """Total for this section."""
        return sum((item.normal_balance for item in self.items), Decimal("0"))


@dataclass
class BalanceSheetReport:
    """Balance Sheet report data."""

    as_of_date: date
    assets_section: BalanceSheetSection = field(
        default_factory=lambda: BalanceSheetSection(title="Assets")
    )
    liabilities_section: BalanceSheetSection = field(
        default_factory=lambda: BalanceSheetSection(title="Liabilities")
    )
    equity_section: BalanceSheetSection = field(
        default_factory=lambda: BalanceSheetSection(title="Equity")
    )
    retained_earnings: Decimal = Decimal("0")

    @property
    def total_assets(self) -> Decimal:
        """Total assets."""
        return self.assets_section.total

    @property
    def total_liabilities(self) -> Decimal:
        """Total liabilities."""
        return self.liabilities_section.total

    @property
    def total_equity(self) -> Decimal:
        """Total equity including retained earnings."""
        return self.equity_section.total + self.retained_earnings

    @property
    def total_liabilities_and_equity(self) -> Decimal:
        """Total liabilities and equity."""
        return self.total_liabilities + self.total_equity

    @property
    def is_balanced(self) -> bool:
        """Check if assets = liabilities + equity."""
        return self.total_assets == self.total_liabilities_and_equity


class BalanceSheetGenerator:
    """
    Domain service for generating Balance Sheet reports.

    The balance sheet shows assets, liabilities, and equity at a point in time.
    """

    def __init__(
        self,
        balance_calculator: BalanceCalculator,
        profit_loss_generator: ProfitLossGenerator
    ) -> None:
        self._balance_calculator = balance_calculator
        self._profit_loss_generator = profit_loss_generator

    def generate(
        self,
        accounts: List[dict],
        as_of_date: date,
        fiscal_year_start: Optional[date] = None
    ) -> BalanceSheetReport:
        """
        Generate a Balance Sheet report.

        Args:
            accounts: List of account dictionaries
            as_of_date: The date for the balance sheet
            fiscal_year_start: Start of fiscal year (for retained earnings)

        Returns:
            BalanceSheetReport object
        """
        # Filter accounts by type
        asset_accounts = [
            a for a in accounts
            if a.get("account_type") == AccountType.ASSET.value
            or a.get("account_type") == AccountType.ASSET
        ]
        liability_accounts = [
            a for a in accounts
            if a.get("account_type") == AccountType.LIABILITY.value
            or a.get("account_type") == AccountType.LIABILITY
        ]
        equity_accounts = [
            a for a in accounts
            if a.get("account_type") == AccountType.EQUITY.value
            or a.get("account_type") == AccountType.EQUITY
        ]

        report = BalanceSheetReport(as_of_date=as_of_date)

        # Calculate asset balances
        if asset_accounts:
            asset_balances = self._balance_calculator.calculate_balances(
                accounts=asset_accounts,
                to_date=as_of_date
            )
            report.assets_section.items = [
                b for b in asset_balances
                if b.debit_total != 0 or b.credit_total != 0
            ]

        # Calculate liability balances
        if liability_accounts:
            liability_balances = self._balance_calculator.calculate_balances(
                accounts=liability_accounts,
                to_date=as_of_date
            )
            report.liabilities_section.items = [
                b for b in liability_balances
                if b.debit_total != 0 or b.credit_total != 0
            ]

        # Calculate equity balances
        if equity_accounts:
            equity_balances = self._balance_calculator.calculate_balances(
                accounts=equity_accounts,
                to_date=as_of_date
            )
            report.equity_section.items = [
                b for b in equity_balances
                if b.debit_total != 0 or b.credit_total != 0
            ]

        # Calculate retained earnings from P&L if fiscal year provided
        if fiscal_year_start:
            pnl = self._profit_loss_generator.generate(
                accounts=accounts,
                from_date=fiscal_year_start,
                to_date=as_of_date
            )
            report.retained_earnings = pnl.net_income

        return report

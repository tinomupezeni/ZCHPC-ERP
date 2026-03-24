"""
Application service for financial reporting.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from modules.accounts.domain.entities import Account
from modules.accounts.domain.value_objects import AccountType
from modules.accounts.domain.services import (
    BalanceCalculator,
    AccountBalance,
    TrialBalance,
    TrialBalanceGenerator,
    ProfitLossReport,
    ProfitLossGenerator,
    BalanceSheetReport,
    BalanceSheetGenerator,
)
from modules.accounts.application.interfaces import (
    IAccountRepository,
    IJournalEntryRepository,
)


@dataclass
class AccountBalanceReport:
    """Balance report for a single account."""

    account_id: int
    account_code: str
    account_name: str
    account_type: str
    opening_balance: Decimal
    total_debit: Decimal
    total_credit: Decimal
    closing_balance: Decimal


@dataclass
class GeneralLedgerEntry:
    """An entry in the general ledger."""

    entry_date: date
    reference: str
    description: str
    debit: Decimal
    credit: Decimal
    running_balance: Decimal


@dataclass
class GeneralLedger:
    """General ledger for an account."""

    account_id: int
    account_code: str
    account_name: str
    from_date: date
    to_date: date
    opening_balance: Decimal
    entries: List[GeneralLedgerEntry]
    closing_balance: Decimal


class ReportingService:
    """
    Application service for financial reporting.

    Generates various financial reports using domain services.
    """

    def __init__(
        self,
        account_repo: IAccountRepository,
        entry_repo: IJournalEntryRepository
    ) -> None:
        self._account_repo = account_repo
        self._entry_repo = entry_repo
        self._balance_calculator = BalanceCalculator(entry_repo)
        self._trial_balance_generator = TrialBalanceGenerator(
            self._balance_calculator
        )
        self._profit_loss_generator = ProfitLossGenerator(
            self._balance_calculator
        )
        self._balance_sheet_generator = BalanceSheetGenerator(
            self._balance_calculator,
            self._profit_loss_generator
        )

    def get_account_balance(
        self,
        account_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> AccountBalanceReport:
        """
        Get balance report for a single account.

        Args:
            account_id: Account ID
            from_date: Optional period start
            to_date: Optional period end

        Returns:
            Account balance report
        """
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            from shared.domain.exceptions import NotFoundError
            raise NotFoundError(f"Account {account_id} not found")

        # Get opening balance (all entries before from_date)
        opening_balance = Decimal("0")
        if from_date:
            opening_lines = self._entry_repo.get_posted_lines_for_account(
                account_id=account_id,
                to_date=from_date
            )
            for line in opening_lines:
                opening_balance += Decimal(str(line.get("debit", 0)))
                opening_balance -= Decimal(str(line.get("credit", 0)))

        # Get period balance
        balance = self._balance_calculator.calculate_balance(
            account_id=account_id,
            account_code=account.code,
            account_name=account.name,
            account_type=account.account_type,
            from_date=from_date,
            to_date=to_date
        )

        closing_balance = opening_balance + balance.balance

        return AccountBalanceReport(
            account_id=account_id,
            account_code=account.code,
            account_name=account.name,
            account_type=account.account_type.value,
            opening_balance=opening_balance,
            total_debit=balance.debit_total,
            total_credit=balance.credit_total,
            closing_balance=closing_balance
        )

    def get_general_ledger(
        self,
        account_id: int,
        from_date: date,
        to_date: date
    ) -> GeneralLedger:
        """
        Get general ledger for an account.

        Shows all transactions with running balance.

        Args:
            account_id: Account ID
            from_date: Period start
            to_date: Period end

        Returns:
            General ledger with entries
        """
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            from shared.domain.exceptions import NotFoundError
            raise NotFoundError(f"Account {account_id} not found")

        # Get opening balance
        opening_lines = self._entry_repo.get_posted_lines_for_account(
            account_id=account_id,
            to_date=from_date
        )
        opening_balance = Decimal("0")
        for line in opening_lines:
            opening_balance += Decimal(str(line.get("debit", 0)))
            opening_balance -= Decimal(str(line.get("credit", 0)))

        # Get period entries
        period_lines = self._entry_repo.get_posted_lines_for_account(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )

        # Build entries with running balance
        running_balance = opening_balance
        entries = []
        for line in sorted(period_lines, key=lambda x: x.get("entry_date", "")):
            debit = Decimal(str(line.get("debit", 0)))
            credit = Decimal(str(line.get("credit", 0)))
            running_balance += debit - credit

            entries.append(GeneralLedgerEntry(
                entry_date=line.get("entry_date"),
                reference=line.get("reference", ""),
                description=line.get("description", ""),
                debit=debit,
                credit=credit,
                running_balance=running_balance
            ))

        return GeneralLedger(
            account_id=account_id,
            account_code=account.code,
            account_name=account.name,
            from_date=from_date,
            to_date=to_date,
            opening_balance=opening_balance,
            entries=entries,
            closing_balance=running_balance
        )

    def get_trial_balance(
        self,
        as_of_date: date,
        from_date: Optional[date] = None
    ) -> TrialBalance:
        """
        Generate trial balance report.

        Args:
            as_of_date: Report date
            from_date: Optional period start

        Returns:
            Trial balance report
        """
        accounts = self._account_repo.get_posting_accounts()
        account_dicts = [
            {
                "id": a.id,
                "code": a.code,
                "name": a.name,
                "account_type": a.account_type
            }
            for a in accounts
        ]

        return self._trial_balance_generator.generate(
            accounts=account_dicts,
            as_of_date=as_of_date,
            from_date=from_date
        )

    def get_profit_loss(
        self,
        from_date: date,
        to_date: date
    ) -> ProfitLossReport:
        """
        Generate Profit & Loss report.

        Args:
            from_date: Period start
            to_date: Period end

        Returns:
            P&L report
        """
        accounts = self._account_repo.get_all()
        account_dicts = [
            {
                "id": a.id,
                "code": a.code,
                "name": a.name,
                "account_type": a.account_type
            }
            for a in accounts
        ]

        return self._profit_loss_generator.generate(
            accounts=account_dicts,
            from_date=from_date,
            to_date=to_date
        )

    def get_balance_sheet(
        self,
        as_of_date: date,
        fiscal_year_start: Optional[date] = None
    ) -> BalanceSheetReport:
        """
        Generate Balance Sheet report.

        Args:
            as_of_date: Report date
            fiscal_year_start: Start of fiscal year (for retained earnings)

        Returns:
            Balance sheet report
        """
        accounts = self._account_repo.get_all()
        account_dicts = [
            {
                "id": a.id,
                "code": a.code,
                "name": a.name,
                "account_type": a.account_type
            }
            for a in accounts
        ]

        return self._balance_sheet_generator.generate(
            accounts=account_dicts,
            as_of_date=as_of_date,
            fiscal_year_start=fiscal_year_start
        )

    def get_account_balances(
        self,
        account_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[AccountBalance]:
        """
        Get balances for multiple accounts.

        Args:
            account_type: Optional type filter
            from_date: Optional period start
            to_date: Optional period end

        Returns:
            List of account balances
        """
        if account_type:
            try:
                parsed_type = AccountType(account_type)
                accounts = self._account_repo.get_by_type(parsed_type)
            except ValueError:
                from shared.domain.exceptions import ValidationError
                raise ValidationError(f"Invalid account type: {account_type}")
        else:
            accounts = self._account_repo.get_posting_accounts()

        account_dicts = [
            {
                "id": a.id,
                "code": a.code,
                "name": a.name,
                "account_type": a.account_type
            }
            for a in accounts
        ]

        return self._balance_calculator.calculate_balances(
            accounts=account_dicts,
            from_date=from_date,
            to_date=to_date
        )

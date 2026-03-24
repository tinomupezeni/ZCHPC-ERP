"""
Balance calculation domain service.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Protocol

from modules.accounts.domain.value_objects import AccountType


class JournalEntryLineReader(Protocol):
    """Protocol for reading journal entry lines."""

    def get_posted_lines_for_account(
        self,
        account_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted journal entry lines for an account."""
        ...

    def get_posted_lines_for_accounts(
        self,
        account_ids: List[int],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted journal entry lines for multiple accounts."""
        ...


@dataclass
class AccountBalance:
    """Represents the balance of an account."""

    account_id: int
    account_code: str
    account_name: str
    account_type: AccountType
    debit_total: Decimal
    credit_total: Decimal

    @property
    def balance(self) -> Decimal:
        """Get the net balance."""
        return self.debit_total - self.credit_total

    @property
    def normal_balance(self) -> Decimal:
        """
        Get the balance in normal form for the account type.

        For debit-normal accounts (Asset, Expense): positive when debit > credit
        For credit-normal accounts (Liability, Equity, Revenue): positive when credit > debit
        """
        if self.account_type in (AccountType.ASSET, AccountType.EXPENSE):
            return self.debit_total - self.credit_total
        else:
            return self.credit_total - self.debit_total

    @property
    def is_debit_balance(self) -> bool:
        """Check if the balance is on the debit side."""
        return self.balance > 0

    @property
    def is_credit_balance(self) -> bool:
        """Check if the balance is on the credit side."""
        return self.balance < 0


class BalanceCalculator:
    """
    Domain service for calculating account balances.

    Calculates balances based on posted journal entry lines.
    """

    def __init__(self, line_reader: JournalEntryLineReader) -> None:
        self._line_reader = line_reader

    def calculate_balance(
        self,
        account_id: int,
        account_code: str,
        account_name: str,
        account_type: AccountType,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> AccountBalance:
        """
        Calculate the balance for a single account.

        Args:
            account_id: The account ID
            account_code: The account code
            account_name: The account name
            account_type: The account type
            from_date: Optional start date
            to_date: Optional end date

        Returns:
            AccountBalance with debit/credit totals
        """
        lines = self._line_reader.get_posted_lines_for_account(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )

        debit_total = Decimal("0")
        credit_total = Decimal("0")

        for line in lines:
            debit_total += Decimal(str(line.get("debit", 0)))
            credit_total += Decimal(str(line.get("credit", 0)))

        return AccountBalance(
            account_id=account_id,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            debit_total=debit_total,
            credit_total=credit_total
        )

    def calculate_balances(
        self,
        accounts: List[dict],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[AccountBalance]:
        """
        Calculate balances for multiple accounts.

        Args:
            accounts: List of account dictionaries with id, code, name, type
            from_date: Optional start date
            to_date: Optional end date

        Returns:
            List of AccountBalance objects
        """
        if not accounts:
            return []

        account_ids = [a["id"] for a in accounts]
        lines = self._line_reader.get_posted_lines_for_accounts(
            account_ids=account_ids,
            from_date=from_date,
            to_date=to_date
        )

        # Group lines by account
        account_lines: Dict[int, List[dict]] = {aid: [] for aid in account_ids}
        for line in lines:
            account_id = line.get("account_id")
            if account_id in account_lines:
                account_lines[account_id].append(line)

        # Calculate balances
        balances = []
        for account in accounts:
            account_id = account["id"]
            account_type = account["account_type"]
            if isinstance(account_type, str):
                account_type = AccountType(account_type)

            debit_total = Decimal("0")
            credit_total = Decimal("0")

            for line in account_lines[account_id]:
                debit_total += Decimal(str(line.get("debit", 0)))
                credit_total += Decimal(str(line.get("credit", 0)))

            balances.append(AccountBalance(
                account_id=account_id,
                account_code=account["code"],
                account_name=account["name"],
                account_type=account_type,
                debit_total=debit_total,
                credit_total=credit_total
            ))

        return balances

    def calculate_partner_balance(
        self,
        account_id: int,
        partner_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate the balance for a specific partner on an account.

        Used for AR/AP tracking.

        Args:
            account_id: The receivable/payable account ID
            partner_id: The partner ID
            from_date: Optional start date
            to_date: Optional end date

        Returns:
            Net balance for the partner
        """
        lines = self._line_reader.get_posted_lines_for_account(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date
        )

        balance = Decimal("0")
        for line in lines:
            if line.get("partner_id") == partner_id:
                balance += Decimal(str(line.get("debit", 0)))
                balance -= Decimal(str(line.get("credit", 0)))

        return balance

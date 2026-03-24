"""
Repository interfaces for the accounts module.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from modules.accounts.domain.entities import (
    Account,
    Currency,
    Journal,
    JournalEntry,
    Partner,
)
from modules.accounts.domain.value_objects import AccountType, JournalType, PartnerType


class IAccountRepository(ABC):
    """Interface for account repository."""

    @abstractmethod
    def save(self, account: Account) -> Account:
        """Save an account."""
        ...

    @abstractmethod
    def get_by_id(self, account_id: int) -> Optional[Account]:
        """Get an account by ID."""
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Account]:
        """Get an account by code."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[Account]:
        """Get all accounts."""
        ...

    @abstractmethod
    def get_by_type(
        self,
        account_type: AccountType,
        include_inactive: bool = False
    ) -> List[Account]:
        """Get accounts by type."""
        ...

    @abstractmethod
    def get_children(self, parent_id: int) -> List[Account]:
        """Get child accounts of a parent."""
        ...

    @abstractmethod
    def get_posting_accounts(self) -> List[Account]:
        """Get all accounts that allow posting."""
        ...

    @abstractmethod
    def delete(self, account_id: int) -> bool:
        """Delete an account."""
        ...

    @abstractmethod
    def exists_by_code(self, code: str) -> bool:
        """Check if an account with the code exists."""
        ...


class ICurrencyRepository(ABC):
    """Interface for currency repository."""

    @abstractmethod
    def save(self, currency: Currency) -> Currency:
        """Save a currency."""
        ...

    @abstractmethod
    def get_by_id(self, currency_id: int) -> Optional[Currency]:
        """Get a currency by ID."""
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Currency]:
        """Get a currency by code."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[Currency]:
        """Get all currencies."""
        ...

    @abstractmethod
    def get_base_currency(self) -> Optional[Currency]:
        """Get the base currency."""
        ...

    @abstractmethod
    def delete(self, currency_id: int) -> bool:
        """Delete a currency."""
        ...


class IJournalRepository(ABC):
    """Interface for journal repository."""

    @abstractmethod
    def save(self, journal: Journal) -> Journal:
        """Save a journal."""
        ...

    @abstractmethod
    def get_by_id(self, journal_id: int) -> Optional[Journal]:
        """Get a journal by ID."""
        ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Journal]:
        """Get a journal by code."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[Journal]:
        """Get all journals."""
        ...

    @abstractmethod
    def get_by_type(
        self,
        journal_type: JournalType,
        include_inactive: bool = False
    ) -> List[Journal]:
        """Get journals by type."""
        ...

    @abstractmethod
    def delete(self, journal_id: int) -> bool:
        """Delete a journal."""
        ...


class IJournalEntryRepository(ABC):
    """Interface for journal entry repository."""

    @abstractmethod
    def save(self, entry: JournalEntry) -> JournalEntry:
        """Save a journal entry with its lines."""
        ...

    @abstractmethod
    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        """Get an entry by ID with all lines."""
        ...

    @abstractmethod
    def get_by_reference(self, reference: str) -> Optional[JournalEntry]:
        """Get an entry by reference."""
        ...

    @abstractmethod
    def get_by_journal(
        self,
        journal_id: int,
        posted_only: bool = False
    ) -> List[JournalEntry]:
        """Get entries for a journal."""
        ...

    @abstractmethod
    def get_by_date_range(
        self,
        from_date: date,
        to_date: date,
        posted_only: bool = False
    ) -> List[JournalEntry]:
        """Get entries in a date range."""
        ...

    @abstractmethod
    def get_posted_lines_for_account(
        self,
        account_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted lines for an account."""
        ...

    @abstractmethod
    def get_posted_lines_for_accounts(
        self,
        account_ids: List[int],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted lines for multiple accounts."""
        ...

    @abstractmethod
    def delete(self, entry_id: int) -> bool:
        """Delete an entry (only if not posted)."""
        ...


class IPartnerRepository(ABC):
    """Interface for partner repository."""

    @abstractmethod
    def save(self, partner: Partner) -> Partner:
        """Save a partner."""
        ...

    @abstractmethod
    def get_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get a partner by ID."""
        ...

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List[Partner]:
        """Get all partners."""
        ...

    @abstractmethod
    def get_by_type(
        self,
        partner_type: PartnerType,
        include_inactive: bool = False
    ) -> List[Partner]:
        """Get partners by type."""
        ...

    @abstractmethod
    def get_customers(self, include_inactive: bool = False) -> List[Partner]:
        """Get all customers."""
        ...

    @abstractmethod
    def get_suppliers(self, include_inactive: bool = False) -> List[Partner]:
        """Get all suppliers."""
        ...

    @abstractmethod
    def search(self, query: str) -> List[Partner]:
        """Search partners by name."""
        ...

    @abstractmethod
    def delete(self, partner_id: int) -> bool:
        """Delete a partner."""
        ...

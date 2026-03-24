"""
Domain events for the accounts module.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from shared.domain.events import DomainEvent


@dataclass(frozen=True)
class AccountCreated(DomainEvent):
    """Event raised when an account is created."""

    account_id: int
    code: str
    name: str
    account_type: str


@dataclass(frozen=True)
class AccountDeactivated(DomainEvent):
    """Event raised when an account is deactivated."""

    account_id: int
    code: str


@dataclass(frozen=True)
class JournalCreated(DomainEvent):
    """Event raised when a journal is created."""

    journal_id: int
    code: str
    name: str
    journal_type: str


@dataclass(frozen=True)
class JournalEntryCreated(DomainEvent):
    """Event raised when a journal entry is created."""

    entry_id: int
    journal_id: int
    entry_date: date
    reference: Optional[str]


@dataclass(frozen=True)
class JournalEntryPosted(DomainEvent):
    """Event raised when a journal entry is posted."""

    entry_id: int
    journal_id: int
    entry_date: date
    total_debit: Decimal
    total_credit: Decimal


@dataclass(frozen=True)
class JournalEntryUnposted(DomainEvent):
    """Event raised when a journal entry is unposted (reversed)."""

    entry_id: int
    journal_id: int


@dataclass(frozen=True)
class PartnerCreated(DomainEvent):
    """Event raised when a partner is created."""

    partner_id: int
    name: str
    partner_type: str


@dataclass(frozen=True)
class PartnerDeactivated(DomainEvent):
    """Event raised when a partner is deactivated."""

    partner_id: int
    name: str


@dataclass(frozen=True)
class CurrencyRateUpdated(DomainEvent):
    """Event raised when a currency exchange rate is updated."""

    currency_id: int
    currency_code: str
    old_rate: Decimal
    new_rate: Decimal


@dataclass(frozen=True)
class AccountReconciled(DomainEvent):
    """Event raised when an account is reconciled."""

    account_id: int
    reconciliation_date: date
    partner_id: Optional[int]
    amount: Decimal

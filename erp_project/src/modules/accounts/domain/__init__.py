"""
Accounts module domain layer.

Contains aggregate roots, entities, value objects, events, and domain services.
"""

from modules.accounts.domain.value_objects import (
    AccountType,
    JournalType,
    PartnerType,
    AccountCode,
    Money,
    DebitCredit,
)
from modules.accounts.domain.entities import (
    Account,
    Currency,
    Journal,
    JournalEntry,
    JournalEntryLine,
    Partner,
)
from modules.accounts.domain.events import (
    AccountCreated,
    AccountDeactivated,
    JournalCreated,
    JournalEntryCreated,
    JournalEntryPosted,
    JournalEntryUnposted,
    PartnerCreated,
    PartnerDeactivated,
    CurrencyRateUpdated,
    AccountReconciled,
)
from modules.accounts.domain.services import (
    AccountBalance,
    BalanceCalculator,
    TrialBalance,
    TrialBalanceGenerator,
    ProfitLossReport,
    ProfitLossGenerator,
    BalanceSheetReport,
    BalanceSheetGenerator,
)

__all__ = [
    # Value objects
    "AccountType",
    "JournalType",
    "PartnerType",
    "AccountCode",
    "Money",
    "DebitCredit",
    # Entities
    "Account",
    "Currency",
    "Journal",
    "JournalEntry",
    "JournalEntryLine",
    "Partner",
    # Events
    "AccountCreated",
    "AccountDeactivated",
    "JournalCreated",
    "JournalEntryCreated",
    "JournalEntryPosted",
    "JournalEntryUnposted",
    "PartnerCreated",
    "PartnerDeactivated",
    "CurrencyRateUpdated",
    "AccountReconciled",
    # Services
    "AccountBalance",
    "BalanceCalculator",
    "TrialBalance",
    "TrialBalanceGenerator",
    "ProfitLossReport",
    "ProfitLossGenerator",
    "BalanceSheetReport",
    "BalanceSheetGenerator",
]

"""
Application layer interfaces for the accounts module.
"""

from modules.accounts.application.interfaces.repositories import (
    IAccountRepository,
    ICurrencyRepository,
    IJournalRepository,
    IJournalEntryRepository,
    IPartnerRepository,
)

__all__ = [
    "IAccountRepository",
    "ICurrencyRepository",
    "IJournalRepository",
    "IJournalEntryRepository",
    "IPartnerRepository",
]

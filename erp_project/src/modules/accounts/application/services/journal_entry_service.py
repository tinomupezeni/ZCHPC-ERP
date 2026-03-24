"""
Application service for journal entry management.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.accounts.domain.entities import JournalEntry, JournalEntryLine
from modules.accounts.domain.events import JournalEntryCreated, JournalEntryPosted
from modules.accounts.application.interfaces import (
    IAccountRepository,
    IJournalRepository,
    IJournalEntryRepository,
)


@dataclass
class JournalEntryLineDTO:
    """DTO for a journal entry line."""

    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    partner_id: Optional[int] = None
    description: Optional[str] = None


@dataclass
class CreateJournalEntryDTO:
    """DTO for creating a journal entry."""

    journal_id: int
    entry_date: date
    lines: List[JournalEntryLineDTO] = field(default_factory=list)
    reference: Optional[str] = None
    narration: Optional[str] = None
    auto_post: bool = False


@dataclass
class UpdateJournalEntryDTO:
    """DTO for updating a journal entry."""

    reference: Optional[str] = None
    narration: Optional[str] = None
    entry_date: Optional[date] = None


class JournalEntryService:
    """
    Application service for managing journal entries.

    Coordinates journal entry operations and enforces double-entry bookkeeping.
    """

    def __init__(
        self,
        entry_repo: IJournalEntryRepository,
        journal_repo: IJournalRepository,
        account_repo: IAccountRepository
    ) -> None:
        self._entry_repo = entry_repo
        self._journal_repo = journal_repo
        self._account_repo = account_repo

    def create_entry(self, dto: CreateJournalEntryDTO) -> JournalEntry:
        """
        Create a new journal entry.

        Args:
            dto: Entry creation data

        Returns:
            Created entry

        Raises:
            ValidationError: If entry is invalid
            NotFoundError: If journal or accounts not found
        """
        # Validate journal exists
        journal = self._journal_repo.get_by_id(dto.journal_id)
        if journal is None:
            raise NotFoundError(f"Journal {dto.journal_id} not found")

        if not journal.is_active:
            raise ValidationError("Cannot create entry in inactive journal")

        # Validate all accounts exist and are posting accounts
        for line_dto in dto.lines:
            account = self._account_repo.get_by_id(line_dto.account_id)
            if account is None:
                raise NotFoundError(f"Account {line_dto.account_id} not found")
            if not account.can_post_entry():
                raise ValidationError(
                    f"Account {account.code} does not allow posting"
                )

        # Create entry
        entry = JournalEntry.create(
            journal_id=dto.journal_id,
            entry_date=dto.entry_date,
            reference=dto.reference,
            narration=dto.narration
        )

        # Add lines
        for line_dto in dto.lines:
            if line_dto.debit > 0:
                entry.add_debit(
                    account_id=line_dto.account_id,
                    amount=line_dto.debit,
                    partner_id=line_dto.partner_id,
                    description=line_dto.description
                )
            elif line_dto.credit > 0:
                entry.add_credit(
                    account_id=line_dto.account_id,
                    amount=line_dto.credit,
                    partner_id=line_dto.partner_id,
                    description=line_dto.description
                )

        # Validate the entry
        entry.validate()

        # Save
        saved_entry = self._entry_repo.save(entry)

        # Auto-post if requested
        if dto.auto_post:
            saved_entry = self.post_entry(saved_entry.id)

        return saved_entry

    def update_entry(
        self,
        entry_id: int,
        dto: UpdateJournalEntryDTO
    ) -> JournalEntry:
        """
        Update an unposted journal entry.

        Args:
            entry_id: ID of entry to update
            dto: Update data

        Returns:
            Updated entry
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        entry.update_details(
            reference=dto.reference,
            narration=dto.narration,
            entry_date=dto.entry_date
        )

        return self._entry_repo.save(entry)

    def add_line_to_entry(
        self,
        entry_id: int,
        line_dto: JournalEntryLineDTO
    ) -> JournalEntry:
        """
        Add a line to an unposted entry.

        Args:
            entry_id: ID of entry
            line_dto: Line data

        Returns:
            Updated entry
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        # Validate account
        account = self._account_repo.get_by_id(line_dto.account_id)
        if account is None:
            raise NotFoundError(f"Account {line_dto.account_id} not found")
        if not account.can_post_entry():
            raise ValidationError(
                f"Account {account.code} does not allow posting"
            )

        # Add line
        if line_dto.debit > 0:
            entry.add_debit(
                account_id=line_dto.account_id,
                amount=line_dto.debit,
                partner_id=line_dto.partner_id,
                description=line_dto.description
            )
        elif line_dto.credit > 0:
            entry.add_credit(
                account_id=line_dto.account_id,
                amount=line_dto.credit,
                partner_id=line_dto.partner_id,
                description=line_dto.description
            )

        return self._entry_repo.save(entry)

    def remove_line_from_entry(
        self,
        entry_id: int,
        line_id: int
    ) -> JournalEntry:
        """
        Remove a line from an unposted entry.

        Args:
            entry_id: ID of entry
            line_id: ID of line to remove

        Returns:
            Updated entry
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        if not entry.remove_line(line_id):
            raise NotFoundError(f"Line {line_id} not found in entry")

        return self._entry_repo.save(entry)

    def post_entry(self, entry_id: int) -> JournalEntry:
        """
        Post a journal entry.

        Args:
            entry_id: ID of entry to post

        Returns:
            Posted entry

        Raises:
            ValidationError: If entry is not balanced
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        entry.post()
        return self._entry_repo.save(entry)

    def unpost_entry(self, entry_id: int) -> JournalEntry:
        """
        Unpost a journal entry (reverse posting).

        Args:
            entry_id: ID of entry to unpost

        Returns:
            Unposted entry
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        entry.unpost()
        return self._entry_repo.save(entry)

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an unposted entry.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted

        Raises:
            ValidationError: If entry is posted
        """
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        if entry.is_posted:
            raise ValidationError("Cannot delete a posted entry")

        return self._entry_repo.delete(entry_id)

    def get_entry(self, entry_id: int) -> JournalEntry:
        """Get an entry by ID."""
        entry = self._entry_repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")
        return entry

    def get_entry_by_reference(self, reference: str) -> JournalEntry:
        """Get an entry by reference."""
        entry = self._entry_repo.get_by_reference(reference)
        if entry is None:
            raise NotFoundError(f"Entry with reference '{reference}' not found")
        return entry

    def list_entries(
        self,
        journal_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        posted_only: bool = False
    ) -> List[JournalEntry]:
        """
        List journal entries with optional filtering.

        Args:
            journal_id: Optional journal filter
            from_date: Optional start date
            to_date: Optional end date
            posted_only: Only include posted entries

        Returns:
            List of entries
        """
        if journal_id is not None:
            return self._entry_repo.get_by_journal(
                journal_id,
                posted_only=posted_only
            )

        if from_date is not None and to_date is not None:
            return self._entry_repo.get_by_date_range(
                from_date,
                to_date,
                posted_only=posted_only
            )

        # Return empty list if no filters - too broad
        return []

    def create_reversing_entry(
        self,
        entry_id: int,
        reversal_date: date,
        reference: Optional[str] = None
    ) -> JournalEntry:
        """
        Create a reversing entry for a posted entry.

        Args:
            entry_id: ID of entry to reverse
            reversal_date: Date for the reversal entry
            reference: Optional reference for reversal

        Returns:
            The reversing entry
        """
        original = self._entry_repo.get_by_id(entry_id)
        if original is None:
            raise NotFoundError(f"Journal entry {entry_id} not found")

        if not original.is_posted:
            raise ValidationError("Can only reverse posted entries")

        # Create reversal entry
        reversal = JournalEntry.create(
            journal_id=original.journal_id,
            entry_date=reversal_date,
            reference=reference or f"REV-{original.reference or entry_id}",
            narration=f"Reversal of entry {original.reference or entry_id}"
        )

        # Swap debits and credits
        for line in original.lines:
            if line.is_debit:
                reversal.add_credit(
                    account_id=line.account_id,
                    amount=line.debit,
                    partner_id=line.partner_id,
                    description=f"Reversal: {line.description or ''}"
                )
            else:
                reversal.add_debit(
                    account_id=line.account_id,
                    amount=line.credit,
                    partner_id=line.partner_id,
                    description=f"Reversal: {line.description or ''}"
                )

        # Validate and save
        reversal.validate()
        saved_reversal = self._entry_repo.save(reversal)

        # Auto-post the reversal
        saved_reversal.post()
        return self._entry_repo.save(saved_reversal)

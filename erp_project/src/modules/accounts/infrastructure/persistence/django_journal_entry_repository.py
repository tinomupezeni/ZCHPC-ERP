"""
Django implementation of journal entry repository.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from modules.accounts.infrastructure.persistence.models import (
    AccountMove as JournalEntryModel,
    AccountMoveLine as JournalEntryLineModel,
)
from modules.accounts.domain.entities import JournalEntry, JournalEntryLine
from modules.accounts.application.interfaces import IJournalEntryRepository


class DjangoJournalEntryRepository(IJournalEntryRepository):
    """Django ORM implementation of journal entry repository."""

    def _line_to_domain(self, model: JournalEntryLineModel) -> JournalEntryLine:
        """Convert line model to domain entity."""
        return JournalEntryLine(
            id=model.id,
            entry_id=model.move_id,
            account_id=model.account_id,
            debit=model.debit,
            credit=model.credit,
            partner_id=model.partner_id,
            currency_id=model.currency_id,
            amount_currency=model.amount_currency,
            analytic_account_id=model.analytic_account_id,
            description=None,  # Legacy model doesn't have description
            line_date=model.date
        )

    def _to_domain(self, model: JournalEntryModel) -> JournalEntry:
        """Convert Django model to domain entity."""
        lines = [
            self._line_to_domain(line)
            for line in model.lines.all()
        ]

        return JournalEntry(
            id=model.id,
            journal_id=model.journal_id,
            entry_date=model.date,
            reference=model.ref,
            narration=model.narration,
            is_posted=model.posted,
            lines=lines,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model_data(self, entry: JournalEntry) -> dict:
        """Convert domain entity to model data."""
        return {
            "journal_id": entry.journal_id,
            "date": entry.entry_date,
            "ref": entry.reference,
            "narration": entry.narration,
            "posted": entry.is_posted,
        }

    def _line_to_model_data(
        self,
        line: JournalEntryLine,
        entry_id: int
    ) -> dict:
        """Convert line domain entity to model data."""
        return {
            "move_id": entry_id,
            "account_id": line.account_id,
            "debit": line.debit,
            "credit": line.credit,
            "partner_id": line.partner_id,
            "currency_id": line.currency_id,
            "amount_currency": line.amount_currency,
            "analytic_account_id": line.analytic_account_id,
            "date": line.line_date or date.today(),
        }

    @transaction.atomic
    def save(self, entry: JournalEntry) -> JournalEntry:
        """Save a journal entry with its lines."""
        data = self._to_model_data(entry)

        if entry.id is None:
            model = JournalEntryModel.objects.create(**data)
            entry_id = model.id
        else:
            JournalEntryModel.objects.filter(id=entry.id).update(**data)
            entry_id = entry.id
            # Delete existing lines to replace with new ones
            JournalEntryLineModel.objects.filter(move_id=entry_id).delete()

        # Create lines
        for line in entry.lines:
            line_data = self._line_to_model_data(line, entry_id)
            JournalEntryLineModel.objects.create(**line_data)

        return self.get_by_id(entry_id)

    def get_by_id(self, entry_id: int) -> Optional[JournalEntry]:
        """Get an entry by ID with all lines."""
        try:
            model = JournalEntryModel.objects.prefetch_related(
                "lines"
            ).get(id=entry_id)
            return self._to_domain(model)
        except JournalEntryModel.DoesNotExist:
            return None

    def get_by_reference(self, reference: str) -> Optional[JournalEntry]:
        """Get an entry by reference."""
        try:
            model = JournalEntryModel.objects.prefetch_related(
                "lines"
            ).get(ref=reference)
            return self._to_domain(model)
        except JournalEntryModel.DoesNotExist:
            return None

    def get_by_journal(
        self,
        journal_id: int,
        posted_only: bool = False
    ) -> List[JournalEntry]:
        """Get entries for a journal."""
        queryset = JournalEntryModel.objects.prefetch_related(
            "lines"
        ).filter(journal_id=journal_id)

        if posted_only:
            queryset = queryset.filter(posted=True)

        return [self._to_domain(m) for m in queryset.order_by("-date")]

    def get_by_date_range(
        self,
        from_date: date,
        to_date: date,
        posted_only: bool = False
    ) -> List[JournalEntry]:
        """Get entries in a date range."""
        queryset = JournalEntryModel.objects.prefetch_related(
            "lines"
        ).filter(date__gte=from_date, date__lte=to_date)

        if posted_only:
            queryset = queryset.filter(posted=True)

        return [self._to_domain(m) for m in queryset.order_by("-date")]

    def get_posted_lines_for_account(
        self,
        account_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted lines for an account."""
        queryset = JournalEntryLineModel.objects.select_related(
            "move"
        ).filter(
            account_id=account_id,
            move__posted=True
        )

        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        return [
            {
                "id": line.id,
                "account_id": line.account_id,
                "partner_id": line.partner_id,
                "debit": line.debit,
                "credit": line.credit,
                "entry_date": line.date,
                "reference": line.move.ref,
                "description": None,
            }
            for line in queryset.order_by("date")
        ]

    def get_posted_lines_for_accounts(
        self,
        account_ids: List[int],
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[dict]:
        """Get posted lines for multiple accounts."""
        queryset = JournalEntryLineModel.objects.select_related(
            "move"
        ).filter(
            account_id__in=account_ids,
            move__posted=True
        )

        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        return [
            {
                "id": line.id,
                "account_id": line.account_id,
                "partner_id": line.partner_id,
                "debit": line.debit,
                "credit": line.credit,
                "entry_date": line.date,
                "reference": line.move.ref,
                "description": None,
            }
            for line in queryset.order_by("date")
        ]

    @transaction.atomic
    def delete(self, entry_id: int) -> bool:
        """Delete an entry (only if not posted)."""
        try:
            entry = JournalEntryModel.objects.get(id=entry_id)
            if entry.posted:
                return False  # Cannot delete posted entry
            entry.delete()
            return True
        except JournalEntryModel.DoesNotExist:
            return False

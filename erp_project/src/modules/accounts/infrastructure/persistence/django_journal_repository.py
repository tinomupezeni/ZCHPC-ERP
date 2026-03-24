"""
Django implementation of journal repository.
"""

from typing import List, Optional

from modules.accounts.infrastructure.persistence.models import Journal as JournalModel
from modules.accounts.domain.entities import Journal
from modules.accounts.domain.value_objects import JournalType
from modules.accounts.application.interfaces import IJournalRepository


class DjangoJournalRepository(IJournalRepository):
    """Django ORM implementation of journal repository."""

    TYPE_TO_DOMAIN = {
        "sale": JournalType.SALE,
        "purchase": JournalType.PURCHASE,
        "cash": JournalType.CASH,
        "bank": JournalType.BANK,
        "general": JournalType.GENERAL,
    }

    TYPE_TO_MODEL = {
        JournalType.SALE: "sale",
        JournalType.PURCHASE: "purchase",
        JournalType.CASH: "cash",
        JournalType.BANK: "bank",
        JournalType.GENERAL: "general",
    }

    def _to_domain(self, model: JournalModel) -> Journal:
        """Convert Django model to domain entity."""
        journal_type = self.TYPE_TO_DOMAIN.get(
            model.journal_type,
            JournalType.GENERAL
        )

        return Journal(
            id=model.id,
            code=model.code,
            name=model.name,
            journal_type=journal_type,
            default_debit_account_id=model.default_debit_account_id,
            default_credit_account_id=model.default_credit_account_id,
            currency_id=model.currency_id,
            is_active=True,  # Legacy model doesn't have is_active
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model_data(self, journal: Journal) -> dict:
        """Convert domain entity to model data."""
        journal_type = self.TYPE_TO_MODEL.get(
            journal.journal_type,
            "general"
        )

        return {
            "code": journal.code,
            "name": journal.name,
            "journal_type": journal_type,
            "default_debit_account_id": journal.default_debit_account_id,
            "default_credit_account_id": journal.default_credit_account_id,
            "currency_id": journal.currency_id,
        }

    def save(self, journal: Journal) -> Journal:
        """Save a journal."""
        data = self._to_model_data(journal)

        if journal.id is None:
            model = JournalModel.objects.create(**data)
        else:
            JournalModel.objects.filter(id=journal.id).update(**data)
            model = JournalModel.objects.get(id=journal.id)

        return self._to_domain(model)

    def get_by_id(self, journal_id: int) -> Optional[Journal]:
        """Get a journal by ID."""
        try:
            model = JournalModel.objects.get(id=journal_id)
            return self._to_domain(model)
        except JournalModel.DoesNotExist:
            return None

    def get_by_code(self, code: str) -> Optional[Journal]:
        """Get a journal by code."""
        try:
            model = JournalModel.objects.get(code=code.upper())
            return self._to_domain(model)
        except JournalModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[Journal]:
        """Get all journals."""
        models = JournalModel.objects.all().order_by("code")
        return [self._to_domain(m) for m in models]

    def get_by_type(
        self,
        journal_type: JournalType,
        include_inactive: bool = False
    ) -> List[Journal]:
        """Get journals by type."""
        model_type = self.TYPE_TO_MODEL.get(journal_type, "general")
        models = JournalModel.objects.filter(
            journal_type=model_type
        ).order_by("code")
        return [self._to_domain(m) for m in models]

    def delete(self, journal_id: int) -> bool:
        """Delete a journal."""
        deleted, _ = JournalModel.objects.filter(id=journal_id).delete()
        return deleted > 0

"""
Django implementation of account repository.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from modules.accounts.infrastructure.persistence.models import AccountChart as AccountModel
from modules.accounts.domain.entities import Account
from modules.accounts.domain.value_objects import AccountType
from modules.accounts.application.interfaces import IAccountRepository


class DjangoAccountRepository(IAccountRepository):
    """Django ORM implementation of account repository."""

    def _to_domain(self, model: AccountModel) -> Account:
        """Convert Django model to domain entity."""
        # Map account type from legacy values
        type_mapping = {
            "view": AccountType.VIEW,
            "regular": AccountType.ASSET,  # Default - would need account code analysis
            "consolidation": AccountType.CONSOLIDATION,
        }
        account_type = type_mapping.get(
            model.account_type,
            AccountType.ASSET
        )

        return Account(
            id=model.id,
            code=model.code,
            name=model.name,
            account_type=account_type,
            parent_id=model.parent_id,
            currency_id=model.currency_id,
            is_reconcilable=model.reconcile,
            is_active=True,  # Legacy model doesn't have is_active
            description=None,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model_data(self, account: Account) -> dict:
        """Convert domain entity to model data."""
        # Map account type to legacy values
        type_mapping = {
            AccountType.VIEW: "view",
            AccountType.CONSOLIDATION: "consolidation",
        }
        account_type = type_mapping.get(account.account_type, "regular")

        return {
            "code": account.code,
            "name": account.name,
            "account_type": account_type,
            "parent_id": account.parent_id,
            "currency_id": account.currency_id,
            "reconcile": account.is_reconcilable,
        }

    def save(self, account: Account) -> Account:
        """Save an account."""
        data = self._to_model_data(account)

        if account.id is None:
            model = AccountModel.objects.create(**data)
        else:
            AccountModel.objects.filter(id=account.id).update(**data)
            model = AccountModel.objects.get(id=account.id)

        return self._to_domain(model)

    def get_by_id(self, account_id: int) -> Optional[Account]:
        """Get an account by ID."""
        try:
            model = AccountModel.objects.get(id=account_id)
            return self._to_domain(model)
        except AccountModel.DoesNotExist:
            return None

    def get_by_code(self, code: str) -> Optional[Account]:
        """Get an account by code."""
        try:
            model = AccountModel.objects.get(code=code)
            return self._to_domain(model)
        except AccountModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[Account]:
        """Get all accounts."""
        # Legacy model doesn't have is_active
        models = AccountModel.objects.all().order_by("code")
        return [self._to_domain(m) for m in models]

    def get_by_type(
        self,
        account_type: AccountType,
        include_inactive: bool = False
    ) -> List[Account]:
        """Get accounts by type."""
        type_mapping = {
            AccountType.VIEW: "view",
            AccountType.CONSOLIDATION: "consolidation",
        }
        legacy_type = type_mapping.get(account_type, "regular")

        models = AccountModel.objects.filter(
            account_type=legacy_type
        ).order_by("code")

        return [self._to_domain(m) for m in models]

    def get_children(self, parent_id: int) -> List[Account]:
        """Get child accounts of a parent."""
        models = AccountModel.objects.filter(
            parent_id=parent_id
        ).order_by("code")
        return [self._to_domain(m) for m in models]

    def get_posting_accounts(self) -> List[Account]:
        """Get all accounts that allow posting (non-view accounts)."""
        models = AccountModel.objects.exclude(
            account_type="view"
        ).order_by("code")
        return [self._to_domain(m) for m in models]

    def delete(self, account_id: int) -> bool:
        """Delete an account."""
        deleted, _ = AccountModel.objects.filter(id=account_id).delete()
        return deleted > 0

    def exists_by_code(self, code: str) -> bool:
        """Check if an account with the code exists."""
        return AccountModel.objects.filter(code=code).exists()

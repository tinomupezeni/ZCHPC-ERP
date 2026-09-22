"""
Django implementation of the assignable budget-code lookup.
"""

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.application.interfaces import IBudgetCodeRepository
from modules.procurement.domain.budget_code_rules import (
    ALLOWED_BUDGET_CODE_EXTERNAL_TYPES,
    BudgetCode,
)


class DjangoBudgetCodeRepository(IBudgetCodeRepository):
    """Filters on external_account_type - never on the structural account_type."""

    def _queryset(self):
        return AccountChart.objects.filter(
            external_account_type__in=ALLOWED_BUDGET_CODE_EXTERNAL_TYPES
        )

    @staticmethod
    def _to_domain(model: AccountChart) -> BudgetCode:
        return BudgetCode(
            id=model.id,
            code=model.code,
            name=model.name,
            external_account_type=model.external_account_type,
        )

    def get_assignable(self) -> list[BudgetCode]:
        return [self._to_domain(m) for m in self._queryset().order_by("code")]

    def get_by_ids(self, budget_code_ids: set[int]) -> dict[int, BudgetCode]:
        if not budget_code_ids:
            return {}
        models = AccountChart.objects.filter(pk__in=budget_code_ids)
        return {m.id: self._to_domain(m) for m in models}

    def get_assignable_by_id(self, budget_code_id: int) -> BudgetCode | None:
        model = self._queryset().filter(pk=budget_code_id).first()
        return self._to_domain(model) if model else None

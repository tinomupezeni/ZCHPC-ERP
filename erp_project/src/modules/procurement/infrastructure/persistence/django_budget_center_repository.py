"""
Django repository implementation for BudgetCenter.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from modules.procurement.infrastructure.persistence.models import BudgetCenter as BudgetCenterModel

from modules.procurement.domain.entities import BudgetCenter
from modules.procurement.application.interfaces import IBudgetCenterRepository


class DjangoBudgetCenterRepository(IBudgetCenterRepository):
    """Django implementation of budget center repository."""

    def _to_domain(self, model: BudgetCenterModel) -> BudgetCenter:
        """Convert Django model to domain entity."""
        return BudgetCenter(
            id=model.id,
            name=model.name,
            code=f"BC-{model.id:04d}",  # Generate code from ID
            allocated_amount=Decimal(str(model.allocated_amount)),
            used_amount=Decimal(str(model.used_amount)),
            fiscal_year=datetime.now().year,  # Not in legacy model
            is_active=True,  # Not in legacy model
        )

    def _to_model(self, entity: BudgetCenter) -> BudgetCenterModel:
        """Convert domain entity to Django model."""
        if entity.id:
            model = BudgetCenterModel.objects.get(pk=entity.id)
        else:
            model = BudgetCenterModel()

        model.name = entity.name
        model.allocated_amount = entity.allocated_amount
        model.used_amount = entity.used_amount
        return model

    def save(self, budget_center: BudgetCenter) -> BudgetCenter:
        """Save a budget center."""
        model = self._to_model(budget_center)
        model.save()
        return self._to_domain(model)

    def get_by_id(self, budget_center_id: int) -> Optional[BudgetCenter]:
        """Get a budget center by ID."""
        try:
            model = BudgetCenterModel.objects.get(pk=budget_center_id)
            return self._to_domain(model)
        except BudgetCenterModel.DoesNotExist:
            return None

    def get_by_code(self, code: str) -> Optional[BudgetCenter]:
        """Get a budget center by code."""
        # Code is generated from ID, so extract ID
        try:
            # Code format: BC-0001
            if code.startswith("BC-"):
                bc_id = int(code[3:])
                return self.get_by_id(bc_id)
        except (ValueError, IndexError):
            pass
        return None

    def get_all(self, include_inactive: bool = False) -> List[BudgetCenter]:
        """Get all budget centers."""
        queryset = BudgetCenterModel.objects.all()
        return [self._to_domain(m) for m in queryset]

    def get_by_fiscal_year(self, year: int) -> List[BudgetCenter]:
        """Get budget centers for a fiscal year."""
        # Legacy model doesn't have fiscal_year, return all
        return self.get_all()

    @transaction.atomic
    def allocate_budget(
        self,
        budget_center_id: int,
        amount: Decimal
    ) -> BudgetCenter:
        """Allocate budget from a budget center."""
        model = BudgetCenterModel.objects.select_for_update().get(
            pk=budget_center_id
        )
        model.used_amount = Decimal(str(model.used_amount)) + amount
        model.save()
        return self._to_domain(model)

    @transaction.atomic
    def release_budget(
        self,
        budget_center_id: int,
        amount: Decimal
    ) -> BudgetCenter:
        """Release allocated budget back to budget center."""
        model = BudgetCenterModel.objects.select_for_update().get(
            pk=budget_center_id
        )
        model.used_amount = max(
            Decimal("0"),
            Decimal(str(model.used_amount)) - amount
        )
        model.save()
        return self._to_domain(model)

    def delete(self, budget_center_id: int) -> bool:
        """Delete a budget center."""
        try:
            model = BudgetCenterModel.objects.get(pk=budget_center_id)
            model.delete()
            return True
        except BudgetCenterModel.DoesNotExist:
            return False

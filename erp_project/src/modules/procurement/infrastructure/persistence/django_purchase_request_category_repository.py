"""
Django implementation of the Purchase Request category repository.
"""

from modules.procurement.application.interfaces import IPurchaseRequestCategoryRepository
from modules.procurement.domain.entities import PurchaseRequestCategory
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory as PurchaseRequestCategoryModel,
)


class DjangoPurchaseRequestCategoryRepository(IPurchaseRequestCategoryRepository):
    """
    Django ORM implementation of the category lookup.

    Reads only - this slice does not expose creating or deactivating a
    category through the application layer at all (that's Finance-curated
    seed data, see the F11-A migrations), so there is no save()/update() here.
    """

    def _to_domain(self, model: PurchaseRequestCategoryModel) -> PurchaseRequestCategory:
        # PurchaseRequestCategory is a @dataclass subclass of AggregateRoot,
        # which is not itself a dataclass - its `id` is not a constructor
        # kwarg (passing id=... here raises TypeError; confirmed against
        # this exact base class). _id is set directly afterward instead,
        # the same way DjangoPurchaseRequestRepository._to_domain does for
        # PurchaseRequest/PurchaseRequestItem.
        category = PurchaseRequestCategory(
            name=model.name,
            account_chart_id=model.account_chart_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        category._id = model.id
        return category

    def get_by_id(self, category_id: int) -> PurchaseRequestCategory | None:
        try:
            model = PurchaseRequestCategoryModel.objects.get(pk=category_id)
        except PurchaseRequestCategoryModel.DoesNotExist:
            return None
        return self._to_domain(model)

    def get_all_active(self) -> list[PurchaseRequestCategory]:
        queryset = PurchaseRequestCategoryModel.objects.filter(is_active=True).order_by("name")
        return [self._to_domain(model) for model in queryset]

    def get_by_account_chart_ids(self, account_chart_ids: set[int]) -> dict[int, PurchaseRequestCategory]:
        if not account_chart_ids:
            return {}
        queryset = PurchaseRequestCategoryModel.objects.filter(account_chart_id__in=account_chart_ids)
        return {model.account_chart_id: self._to_domain(model) for model in queryset}

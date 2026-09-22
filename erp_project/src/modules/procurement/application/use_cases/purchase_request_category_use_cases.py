"""
Purchase Request Category Application Use Cases (Slice F11-A).

Read-only: the only use case here lists the categories an employee may
currently choose from. Resolving a chosen category into a budget_code_id
happens inside CreatePurchaseRequest itself
(modules.procurement.application.use_cases.purchase_request_use_cases) -
not here - since that's part of the create workflow, not a separate
category operation.
"""

from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.application.interfaces import IPurchaseRequestCategoryRepository
from modules.procurement.domain.entities import PurchaseRequestCategory


class ListActivePurchaseRequestCategories:
    """
    List the categories currently selectable by a requester.

    Authorization mirrors CreatePurchaseRequest's own gate deliberately:
    seeing the category list is only useful to someone who could actually
    use one to raise a request, so this requires the same `create`
    capability rather than a new permission being introduced for it.
    """

    def __init__(
        self,
        repository: IPurchaseRequestCategoryRepository,
        policy: PurchaseRequestAuthorizationPolicy,
    ) -> None:
        self.repository = repository
        self.policy = policy

    def execute(self, actor: Actor) -> list[PurchaseRequestCategory]:
        self.policy.authorize_list_categories(actor)
        return self.repository.get_all_active()

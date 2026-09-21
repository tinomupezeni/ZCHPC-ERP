"""
Accounts budget-code assignment (F25 Slice 2).

Accounts owns the authoritative PurchaseRequestItem.budget_code_id. These use
cases let Accounts see which AccountChart rows are assignable and assign one
per item while a request is PENDING_ACCOUNTS.
"""

from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.application.interfaces import (
    IBudgetCodeRepository,
    IPurchaseRequestRepository,
)
from modules.procurement.application.use_cases.purchase_request_use_cases import (
    BasePurchaseRequestUseCase,
)
from modules.procurement.domain.budget_code_rules import BudgetCode
from modules.procurement.domain.entities import PurchaseRequest
from shared.domain.exceptions import ValidationError


class ListAssignableBudgetCodes:
    def __init__(
        self,
        repository: IBudgetCodeRepository,
        policy: PurchaseRequestAuthorizationPolicy,
    ) -> None:
        self.repository = repository
        self.policy = policy

    def execute(self, actor: Actor) -> list[BudgetCode]:
        self.policy.authorize_list_budget_codes(actor)
        return self.repository.get_assignable()


class AssignItemBudgetCode(BasePurchaseRequestUseCase):
    """
    Assign one item's budget code.

    The chosen code must be an assignable AccountChart (Revenue / Other Income
    / Other Expense by external_account_type). Validated before the aggregate
    is touched, so a bad choice changes nothing.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        budget_code_repository: IBudgetCodeRepository,
    ) -> None:
        super().__init__(repository, policy)
        self.budget_code_repository = budget_code_repository

    def execute(
        self, request_id: int, item_id: int, budget_code_id: int, actor: Actor
    ) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_budget_code_assignment(actor, request)

        if self.budget_code_repository.get_assignable_by_id(budget_code_id) is None:
            raise ValidationError(
                f"Budget code {budget_code_id} is not an assignable account",
                code="BUDGET_CODE_NOT_ALLOWED",
            )

        request.assign_budget_code(item_id, budget_code_id)
        return self.repository.save(request)

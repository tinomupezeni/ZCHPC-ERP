"""
Purchase Request Application Use Cases.

These classes orchestrate the business workflow for purchase requests
by delegating domain rules to the aggregate root and persisting
changes via the repository.

Each use case authorizes the acting employee before invoking the domain:

    authorize actor -> load aggregate -> authorize actor for this record
    -> invoke domain method -> save aggregate

Authorization lives entirely in PurchaseRequestAuthorizationPolicy; the domain
remains authoritative over which state transitions are legal.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

from shared.domain.exceptions import NotFoundError
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
    PurchaseRequestListScope,
)
from modules.procurement.application.interfaces import (
    IOrganizationalDirectory,
    IPurchaseRequestRepository,
)


@dataclass
class PurchaseRequestItemDTO:
    """DTO for creating a purchase request item."""

    description: str
    quantity: int
    expected_delivery_period: str
    estimated_cost: Decimal
    budget_code_id: int


@dataclass
class CreatePurchaseRequestDTO:
    """DTO for creating a purchase request."""

    requester_id: int
    requester_name: str
    department_id: int
    department_name: str
    designation: str
    contact: str
    items: List[PurchaseRequestItemDTO] = field(default_factory=list)


class BasePurchaseRequestUseCase:
    """
    Shared wiring for authorized purchase request use cases.

    The policy is a required collaborator so that no use case can be
    constructed without an authorization decision point.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
    ) -> None:
        self.repository = repository
        self.policy = policy

    def _load(self, request_id: int, actor: Actor) -> PurchaseRequest:
        """
        Load the aggregate for an authenticated actor.

        Authentication is checked first so an anonymous caller cannot learn
        whether a given purchase request exists.
        """
        self.policy.require_authenticated(actor)

        request = self.repository.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")
        return request


class CreatePurchaseRequest(BasePurchaseRequestUseCase):
    def execute(self, dto: CreatePurchaseRequestDTO, actor: Actor) -> PurchaseRequest:
        self.policy.authorize_create(actor, requester_id=dto.requester_id)

        request = PurchaseRequest.create(
            requester_id=dto.requester_id,
            requester_name=dto.requester_name,
            department_id=dto.department_id,
            department_name=dto.department_name,
            designation=dto.designation,
            contact=dto.contact,
        )

        for item_dto in dto.items:
            item = PurchaseRequestItem(
                description=item_dto.description,
                quantity=item_dto.quantity,
                expected_delivery_period=item_dto.expected_delivery_period,
                estimated_cost=item_dto.estimated_cost,
                budget_code_id=item_dto.budget_code_id,
            )
            request.add_item(item)

        return self.repository.save(request)


class ViewPurchaseRequest(BasePurchaseRequestUseCase):
    """Read a single purchase request."""

    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_view(actor, request)
        return request


class ListPurchaseRequests(BasePurchaseRequestUseCase):
    """
    Read a named collection of purchase requests.

    Listing is always scoped - there is no "all requests" collection. MINE
    returns the actor's own; each workflow queue returns the requests waiting
    at that stage, and the department head queue is narrowed to the departments
    the actor is actually recorded as heading.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        directory: IOrganizationalDirectory | None = None,
    ) -> None:
        super().__init__(repository, policy)
        self.directory = directory

    def execute(
        self,
        actor: Actor,
        scope: PurchaseRequestListScope = PurchaseRequestListScope.MINE,
    ) -> List[PurchaseRequest]:
        self.policy.authorize_list(actor, scope)

        if scope is PurchaseRequestListScope.MINE:
            return self.repository.get_by_requester(actor.employee_id)

        if scope is PurchaseRequestListScope.PENDING_DEPARTMENT_HEAD:
            pending = self.repository.get_pending_department_head()
            return self._only_headed_departments(actor, pending)

        return _QUEUE_READERS[scope](self.repository)

    def _only_headed_departments(
        self, actor: Actor, requests: List[PurchaseRequest]
    ) -> List[PurchaseRequest]:
        """
        Narrow the department head queue to what this actor could act on.

        Mirrors the authorization rule rather than restating it: a request the
        policy would refuse is a request the actor should not see queued.
        """
        if actor.is_admin:
            return requests
        if self.directory is None or actor.employee_id is None:
            return []

        headed = self.directory.get_headed_department_ids(actor.employee_id)
        return [r for r in requests if r.department_id in headed]


_QUEUE_READERS = {
    PurchaseRequestListScope.PENDING_ACCOUNTS: lambda repo: repo.get_pending_accounts(),
    PurchaseRequestListScope.PENDING_GM: lambda repo: repo.get_pending_gm(),
    PurchaseRequestListScope.PENDING_DIRECTOR: lambda repo: repo.get_pending_director(),
    PurchaseRequestListScope.PENDING_PROCUREMENT: (
        lambda repo: repo.get_pending_procurement()
    ),
}


class SubmitPurchaseRequest(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_submit(actor, request)

        request.submit()
        return self.repository.save(request)


class ApprovePurchaseRequestByDepartmentHead(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_department_head_approval(actor, request)

        request.approve_by_department_head(actor.employee_id)
        return self.repository.save(request)


class VerifyPurchaseRequestByAccounts(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_accounts_verification(actor, request)

        request.verify_by_accounts(actor.employee_id)
        return self.repository.save(request)


class RecommendPurchaseRequestByGM(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_gm_recommendation(actor, request)

        request.recommend_by_gm(actor.employee_id)
        return self.repository.save(request)


class ApprovePurchaseRequestByDirector(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_director_approval(actor, request)

        request.approve_by_director(actor.employee_id)
        return self.repository.save(request)


class ProcessPurchaseRequestByProcurement(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_processing(actor, request)

        request.process_by_procurement(actor.employee_id)
        return self.repository.save(request)


class RejectPurchaseRequest(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor, reason: str) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_rejection(actor, request)

        request.reject(actor.employee_id, reason)
        return self.repository.save(request)


class CorrectAndResubmitPurchaseRequest(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_correction_and_resubmission(actor, request)

        request.correct_and_resubmit()
        return self.repository.save(request)

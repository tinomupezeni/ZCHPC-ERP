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

from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
    PurchaseRequestListScope,
)
from modules.procurement.application.interfaces import (
    IOrganizationalDirectory,
    IPurchaseRequestCategoryRepository,
    IPurchaseRequestRepository,
)
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from shared.domain.exceptions import NotFoundError, ValidationError
from shared.infrastructure import EventBus, get_event_bus


def resolve_budget_code_id(
    category_repository: IPurchaseRequestCategoryRepository,
    category_id: int | None,
    budget_code_id: int | None,
) -> int:
    """
    Resolve one item's budget_code_id from either an employee-facing
    category_id or a direct budget_code_id.

    category_id always wins when present, even if budget_code_id was also
    somehow supplied: the employee-facing category path must be the one
    actually in control of the resulting GL account. This is the enforcement
    point for "an ordinary employee must not be able to choose an arbitrary
    AccountChart ID" - not the serializer, which is just the first line of
    defence.

    Shared by CreatePurchaseRequest and UpdatePurchaseRequestItems (Slice 2)
    so this security-critical rule lives in exactly one place rather than two
    copies that could silently drift apart. No keyword matching, no
    description-based inference, no AccountChart code-prefix or account_type
    logic - PurchaseRequestCategory is the sole, Finance-curated source of
    truth (see the F11 investigation for why those alternatives were
    rejected).
    """
    if category_id is not None:
        category = category_repository.get_by_id(category_id)
        if category is None:
            raise ValidationError(
                f"Purchase request category {category_id} does not exist",
                code="CATEGORY_NOT_FOUND",
            )
        if not category.is_active:
            raise ValidationError(
                f"Purchase request category {category_id} is not active",
                code="CATEGORY_INACTIVE",
            )
        return category.account_chart_id

    if budget_code_id is not None:
        return budget_code_id

    raise ValidationError(
        "Each item requires either category_id or budget_code_id",
        code="MISSING_BUDGET_CLASSIFICATION",
    )


@dataclass
class PurchaseRequestItemDTO:
    """
    DTO for creating a purchase request item.

    Exactly one of category_id/budget_code_id must be supplied per item -
    CreatePurchaseRequest resolves category_id to a budget_code_id itself
    (Slice F11-A); neither field is meant to be optional in the sense of
    "may be left out entirely". budget_code_id stays direct-FK, unchanged
    from before this slice, for callers that already know the exact
    AccountChart row (e.g. back-office/admin use) - see
    CreatePurchaseRequest._resolve_budget_code_id for exactly how the two
    inputs are reconciled and which one wins if both are somehow present.
    """

    description: str
    quantity: int
    expected_delivery_period: str
    estimated_cost: Decimal
    budget_code_id: int | None = None
    category_id: int | None = None


@dataclass
class CreatePurchaseRequestDTO:
    """DTO for creating a purchase request."""

    requester_id: int
    requester_name: str
    department_id: int
    department_name: str
    designation: str
    contact: str
    items: list[PurchaseRequestItemDTO] = field(default_factory=list)


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
    """
    Creates a draft purchase request.

    category_repository is what makes Slice F11-A's employee-facing category
    selection possible: each item's category_id (if supplied) is resolved to
    a concrete budget_code_id here, before the domain entity is ever built.
    PurchaseRequestItem itself is unchanged - it still only ever receives a
    plain budget_code_id int, exactly as before this slice.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        category_repository: IPurchaseRequestCategoryRepository,
    ) -> None:
        super().__init__(repository, policy)
        self.category_repository = category_repository

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
                budget_code_id=self._resolve_budget_code_id(item_dto),
            )
            request.add_item(item)

        return self.repository.save(request)

    def _resolve_budget_code_id(self, item_dto: "PurchaseRequestItemDTO") -> int:
        """See resolve_budget_code_id - this is a thin instance-method wrapper."""
        return resolve_budget_code_id(
            self.category_repository, item_dto.category_id, item_dto.budget_code_id
        )


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
    ) -> list[PurchaseRequest]:
        self.policy.authorize_list(actor, scope)

        if scope is PurchaseRequestListScope.MINE:
            return self.repository.get_by_requester(actor.employee_id)

        if scope is PurchaseRequestListScope.PENDING_DEPARTMENT_HEAD:
            pending = self.repository.get_pending_department_head()
            return self._only_headed_departments(actor, pending)

        return _QUEUE_READERS[scope](self.repository)

    def _only_headed_departments(
        self, actor: Actor, requests: list[PurchaseRequest]
    ) -> list[PurchaseRequest]:
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
    """
    F19: publishes PurchaseRequestCorrectedAndResubmitted after a successful
    save, but only when this submit is a corrected resubmission - see
    PurchaseRequest.submit()'s own docstring for how it decides that. A
    first-time submission raises no domain event and this publishes nothing,
    identical to the pre-F19 behavior. event_bus defaults to the process-wide
    singleton, matching RejectPurchaseRequest/ProcessPurchaseRequestByProcurement
    so existing 2-arg call sites (e.g. the API view) keep working unchanged.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(repository, policy)
        self._event_bus = event_bus or get_event_bus()

    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_submit(actor, request)

        request.submit()
        saved = self.repository.save(request)
        self._event_bus.publish_all(request.clear_domain_events())
        return saved


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
    """
    Slice 3: publishes PurchaseRequestProcessed after a successful save, so
    modules.portal can react by notifying the requester - see
    modules/portal/event_handlers.py. event_bus defaults to the process-wide
    singleton (matching modules/hr/application/services/employee_service.py's
    injection pattern) so existing 2-arg call sites keep working unchanged.

    Domain events must be read from `request` (the object process_by_procurement
    was called on), not from this method's return value: the repository's
    save() reconstructs and returns a brand new PurchaseRequest from the
    database, whose own _domain_events starts empty.

    Known limitation - dual write, no outbox (accepted for Slice 3):
    repository.save() and event_bus.publish_all() are two separate,
    non-atomic operations, not one transaction. The status transition is
    durably committed by save(); the notification is a best-effort side
    effect published immediately afterwards. If the process crashes or is
    killed in the narrow window between those two calls, the request is
    left correctly PROCESSED/REJECTED but the requester's notification is
    never created - there is no persisted record that an event was "owed",
    so nothing retries or backfills it. Separately, the event bus's default
    non-strict mode (see shared/infrastructure/event_bus.py) catches and
    only logs exceptions raised inside a handler, so if
    modules.portal.event_handlers itself fails to write the Notification
    row (e.g. a DB error), that failure is silent from this use case's
    point of view too - execute() still returns success, because the
    workflow transition itself did succeed and must not be rolled back or
    reported as failed on account of a missed notification.
    A transactional outbox (writing the event in the same DB transaction as
    the status change, then dispatching it separately with retries) would
    close this gap, but is intentionally out of scope here: this slice's
    brief was to make notifications functional on top of the existing
    event bus, not to redesign how the event system guarantees delivery.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(repository, policy)
        self._event_bus = event_bus or get_event_bus()

    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_processing(actor, request)

        request.process_by_procurement(actor.employee_id)
        saved = self.repository.save(request)
        self._event_bus.publish_all(request.clear_domain_events())
        return saved


class RejectPurchaseRequest(BasePurchaseRequestUseCase):
    """Slice 3: publishes PurchaseRequestRejected after a successful save - see ProcessPurchaseRequestByProcurement's docstring for why."""

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(repository, policy)
        self._event_bus = event_bus or get_event_bus()

    def execute(self, request_id: int, actor: Actor, reason: str) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_rejection(actor, request)

        request.reject(actor.employee_id, reason)
        saved = self.repository.save(request)
        self._event_bus.publish_all(request.clear_domain_events())
        return saved


class CorrectAndResubmitPurchaseRequest(BasePurchaseRequestUseCase):
    def execute(self, request_id: int, actor: Actor) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_correction_and_resubmission(actor, request)

        request.correct_and_resubmit()
        return self.repository.save(request)


@dataclass
class UpdatePurchaseRequestItemDTO:
    """
    DTO for one item in a Slice 2 item-collection replacement.

    Unlike PurchaseRequestItemDTO, there is no budget_code_id field at all -
    this use case is exclusively the employee-facing edit path, so the
    direct-GL escape hatch CreatePurchaseRequest keeps for back-office
    callers has no reason to exist here. `id` identifies an existing item on
    the request to update; leave it None for a new item.
    """

    description: str
    quantity: int
    expected_delivery_period: str
    estimated_cost: Decimal
    category_id: int
    id: int | None = None


class UpdatePurchaseRequestItems(BasePurchaseRequestUseCase):
    """
    Replace a DRAFT or REJECTED request's entire item collection (Slice 2).

    REJECTED is handled by composing two existing, unmodified, single-purpose
    domain operations into one atomic save - never by teaching replace_items
    a second responsibility:

        correct_and_resubmit()  # REJECTED -> DRAFT, only reached here
        replace_items(...)       # DRAFT-only; now legal either way

    This means the REJECTED -> DRAFT transition only ever happens together
    with an actual saved correction: if anything below raises (unknown item
    id, invalid category, ...), it does so before either domain method is
    called, so a failed edit leaves a REJECTED request exactly as REJECTED as
    it was, not silently demoted to an unflagged draft.
    """

    def __init__(
        self,
        repository: IPurchaseRequestRepository,
        policy: PurchaseRequestAuthorizationPolicy,
        category_repository: IPurchaseRequestCategoryRepository,
    ) -> None:
        super().__init__(repository, policy)
        self.category_repository = category_repository

    def execute(
        self,
        request_id: int,
        items: list[UpdatePurchaseRequestItemDTO],
        actor: Actor,
    ) -> PurchaseRequest:
        request = self._load(request_id, actor)
        self.policy.authorize_edit(actor, request)

        existing_ids = {item.id for item in request.items}
        seen_ids: set[int] = set()
        new_items: list[PurchaseRequestItem] = []

        for item_dto in items:
            if item_dto.id is not None:
                if item_dto.id in seen_ids:
                    raise ValidationError(
                        f"Duplicate item id {item_dto.id}", code="DUPLICATE_ITEM_ID"
                    )
                if item_dto.id not in existing_ids:
                    raise ValidationError(
                        f"Item {item_dto.id} does not belong to this request",
                        code="ITEM_NOT_FOUND",
                    )
                seen_ids.add(item_dto.id)

            item = PurchaseRequestItem(
                description=item_dto.description,
                quantity=item_dto.quantity,
                expected_delivery_period=item_dto.expected_delivery_period,
                estimated_cost=item_dto.estimated_cost,
                budget_code_id=resolve_budget_code_id(
                    self.category_repository, item_dto.category_id, None
                ),
            )
            if item_dto.id is not None:
                item._id = item_dto.id
            new_items.append(item)

        if request.status == RequestStatus.REJECTED:
            request.correct_and_resubmit()

        request.replace_items(new_items)
        return self.repository.save(request)


class DeletePurchaseRequest(BasePurchaseRequestUseCase):
    """
    Permanently delete a draft (Slice 4).

    Deletion is not a state transition, so there is no domain method to
    invoke - the legality checks below live here rather than on
    PurchaseRequest, mirroring how ViewPurchaseRequest/ListPurchaseRequests
    (also non-mutating) don't call the domain either. authorize_delete only
    decides permission + ownership; DRAFT-only and no-decision-history are
    business rules about *this* operation, not about who the actor is, so
    they stay in the use case rather than the policy.

    A DRAFT that already carries decision history (rejected, then corrected
    back to DRAFT via correct_and_resubmit - which never clears
    request.decisions) is deliberately excluded: the persistence layer
    cascade-deletes PurchaseRequestDecision rows along with the request,
    which would silently destroy the approval/rejection audit trail the
    data model's own docstring says must never be overwritten. Such a
    request must be corrected and resubmitted, not deleted.
    """

    def execute(self, request_id: int, actor: Actor) -> None:
        request = self._load(request_id, actor)
        self.policy.authorize_delete(actor, request)

        if request.status != RequestStatus.DRAFT:
            raise ValidationError(
                f"Cannot delete a request in status {request.status.value}",
                code="NOT_DELETABLE",
            )
        if request.decisions:
            raise ValidationError(
                "Cannot delete a request with decision history - correct and "
                "resubmit it instead",
                code="HAS_DECISION_HISTORY",
            )

        if not self.repository.delete(request_id):
            raise NotFoundError(f"Purchase request {request_id} not found")

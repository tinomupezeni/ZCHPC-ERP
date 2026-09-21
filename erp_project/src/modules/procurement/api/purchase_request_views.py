"""
API views for the redesigned Purchase Request workflow.

Every view is a thin adapter: validate the request shape, resolve the
authenticated actor, invoke one application use case, serialize the result.

Authorization belongs to the Slice 4 policy and state transitions to the
PurchaseRequest aggregate - neither is reproduced here. No view reads an
acting identity from the request body.
"""

from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from modules.procurement.api.actors import actor_from_request, requester_identity
from modules.procurement.api.purchase_request_serializers import (
    AssignBudgetCodeInputSerializer,
    BudgetCodeSerializer,
    CreatePurchaseRequestInputSerializer,
    ListPurchaseRequestsQuerySerializer,
    ProcessPurchaseRequestInputSerializer,
    PurchaseRequestCategorySerializer,
    PurchaseRequestListSerializer,
    PurchaseRequestSerializer,
    RejectPurchaseRequestInputSerializer,
    UpdatePurchaseRequestInputSerializer,
)
from modules.procurement.application.authorization import (
    PurchaseRequestAuthorizationPolicy,
    PurchaseRequestPermissions,
)
from modules.procurement.application.use_cases import (
    AssignItemBudgetCode,
    ListAssignableBudgetCodes,
    ApprovePurchaseRequestByDepartmentHead,
    ApprovePurchaseRequestByDirector,
    CorrectAndResubmitPurchaseRequest,
    CreatePurchaseRequest,
    CreatePurchaseRequestDTO,
    DeletePurchaseRequest,
    ListActivePurchaseRequestCategories,
    ListPurchaseRequests,
    ProcessPurchaseRequestByProcurement,
    PurchaseRequestItemDTO,
    RecommendPurchaseRequestByGM,
    RejectPurchaseRequest,
    SubmitPurchaseRequest,
    UpdatePurchaseRequestItemDTO,
    UpdatePurchaseRequestItems,
    VerifyPurchaseRequestByAccounts,
    ViewPurchaseRequest,
)
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from modules.procurement.infrastructure.persistence.django_budget_code_repository import (
    DjangoBudgetCodeRepository,
)
from modules.procurement.infrastructure.persistence.django_purchase_request_category_repository import (
    DjangoPurchaseRequestCategoryRepository,
)
from modules.procurement.infrastructure.persistence.django_purchase_request_repository import (
    DjangoPurchaseRequestRepository,
)
from shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainException,
    NotFoundError,
    ValidationError,
)

# Composition root for the purchase request slice.
_repository = DjangoPurchaseRequestRepository()
_directory = DjangoOrganizationalDirectory()
_policy = PurchaseRequestAuthorizationPolicy(directory=_directory)
_category_repository = DjangoPurchaseRequestCategoryRepository()
_budget_code_repository = DjangoBudgetCodeRepository()


def _handle_domain_error(exc: DomainException) -> Response:
    """
    Map application/domain failures onto HTTP status codes.

    A failure is never reported as success; the narrowest accurate status wins.
    """
    if isinstance(exc, AuthorizationError):
        http_status = (
            status.HTTP_401_UNAUTHORIZED
            if exc.code == "UNAUTHENTICATED"
            else status.HTTP_403_FORBIDDEN
        )
    elif isinstance(exc, NotFoundError):
        http_status = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ConflictError):
        http_status = status.HTTP_409_CONFLICT
    elif isinstance(exc, ValidationError | BusinessRuleViolationError):
        http_status = status.HTTP_400_BAD_REQUEST
    else:
        http_status = status.HTTP_400_BAD_REQUEST

    return Response({"error": exc.message, "code": exc.code}, status=http_status)


def _categories_by_id(items) -> dict:
    """One batched lookup per response instead of one query per item."""
    return _category_repository.get_by_ids({item.category_id for item in items})


def _budget_codes_by_id(items) -> dict:
    """One batched lookup of the assigned budget codes, by each item's own budget_code_id."""
    return _budget_code_repository.get_by_ids(
        {item.budget_code_id for item in items if item.budget_code_id is not None}
    )


def _may_see_budget_codes(actor) -> bool:
    """
    The one place that decides who receives the Accounts-assigned budget code.

    Finance (accounts_verify) and Procurement (process) only. Every other
    caller - including the requester of the very request - gets neither
    budget_code nor budget_code_id.
    """
    return actor.has_permission(
        PurchaseRequestPermissions.ACCOUNTS_VERIFY
    ) or actor.has_permission(PurchaseRequestPermissions.PROCESS)


def _serialize_request(result, request: Request) -> dict:
    """
    The single place a PurchaseRequest becomes a response body, so every
    response - create, detail, submit, every approval stage, reject,
    correct-and-resubmit, and now the Slice 2 edit endpoint - consistently
    includes each item's reverse-resolved category (Slice 2).

    Tolerates result=None: PurchaseRequestSerializer's fields are all
    read_only (implicitly not required), so DRF already serializes a None
    instance to a degenerate value rather than raising - existing
    TestApplicationBoundary tests mock a use case's return value as None to
    test call-argument wiring only, and rely on exactly that. Building the
    category map must not be the thing that breaks that tolerance.
    """
    items = result.items if result is not None else []
    include_budget_code = _may_see_budget_codes(actor_from_request(request))
    context = {
        "categories_by_id": _categories_by_id(items),
        "include_budget_code": include_budget_code,
        # Only look the codes up when they will actually be returned.
        "budget_codes_by_id": (
            _budget_codes_by_id(items) if include_budget_code else {}
        ),
    }
    return PurchaseRequestSerializer(result, context=context).data


def _workflow_action(request: Request, request_id: int, use_case_cls) -> Response:
    """Run a no-payload workflow transition and return the updated request."""
    use_case = use_case_cls(_repository, _policy)
    try:
        result = use_case.execute(request_id, actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request))


@api_view(["GET", "POST"])
def purchase_request_list(request: Request) -> Response:
    """List the caller's purchase requests (or a workflow queue), or raise one."""
    if request.method == "GET":
        query = ListPurchaseRequestsQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = ListPurchaseRequests(_repository, _policy, _directory)
        try:
            results = use_case.execute(
                actor_from_request(request), query.validated_scope()
            )
        except DomainException as exc:
            return _handle_domain_error(exc)

        return Response(PurchaseRequestListSerializer(results, many=True).data)

    serializer = CreatePurchaseRequestInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    actor = actor_from_request(request)
    employee = getattr(request.user, "employee_profile", None)
    if employee is None:
        return _handle_domain_error(
            AuthorizationError(
                "Raising a purchase request requires an employee profile",
                code="NO_EMPLOYEE_PROFILE",
            )
        )

    dto = CreatePurchaseRequestDTO(
        **requester_identity(actor, employee),
        items=[
            PurchaseRequestItemDTO(
                description=item["description"],
                quantity=item["quantity"],
                expected_delivery_period=item["expected_delivery_period"],
                estimated_cost=Decimal(item["estimated_cost"]),
                category_id=item["category_id"],
            )
            for item in serializer.validated_data["items"]
        ],
    )

    try:
        result = CreatePurchaseRequest(
            _repository, _policy, _category_repository
        ).execute(dto, actor)
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request), status=status.HTTP_201_CREATED)


@api_view(["GET"])
def purchase_request_categories_list(request: Request) -> Response:
    """
    List the Purchase Request categories currently selectable by the caller
    (Slice F11-A).

    Employee-facing only: id + name, nothing about the underlying
    AccountChart row. Requires the same capability as raising a request
    (see PurchaseRequestAuthorizationPolicy.authorize_list_categories) -
    this is deliberately not routed through /api/v2/accounts/*, which
    ordinary requesters are not, and should not be, granted access to.
    """
    use_case = ListActivePurchaseRequestCategories(_category_repository, _policy)
    try:
        results = use_case.execute(actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(PurchaseRequestCategorySerializer(results, many=True).data)


@api_view(["GET", "PATCH", "DELETE"])
def purchase_request_detail(request: Request, request_id: int) -> Response:
    """
    Retrieve a single purchase request, (PATCH) replace a DRAFT/REJECTED
    request's entire item collection (Slice 2 - see UpdatePurchaseRequestItems
    for how REJECTED is handled), or (DELETE) permanently remove a clean
    draft (Slice 4 - see DeletePurchaseRequest for what "clean" means).
    """
    if request.method == "DELETE":
        delete_use_case = DeletePurchaseRequest(_repository, _policy)
        try:
            delete_use_case.execute(request_id, actor_from_request(request))
        except DomainException as exc:
            return _handle_domain_error(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == "PATCH":
        serializer = UpdatePurchaseRequestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dto_items = [
            UpdatePurchaseRequestItemDTO(
                id=item.get("id"),
                description=item["description"],
                quantity=item["quantity"],
                expected_delivery_period=item["expected_delivery_period"],
                estimated_cost=Decimal(item["estimated_cost"]),
                category_id=item["category_id"],
            )
            for item in serializer.validated_data["items"]
        ]

        update_use_case = UpdatePurchaseRequestItems(
            _repository, _policy, _category_repository
        )
        try:
            result = update_use_case.execute(
                request_id, dto_items, actor_from_request(request)
            )
        except DomainException as exc:
            return _handle_domain_error(exc)

        return Response(_serialize_request(result, request))

    use_case = ViewPurchaseRequest(_repository, _policy)
    try:
        result = use_case.execute(request_id, actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request))


@api_view(["POST"])
def purchase_request_submit(request: Request, request_id: int) -> Response:
    """Submit a draft purchase request into the approval workflow."""
    return _workflow_action(request, request_id, SubmitPurchaseRequest)


@api_view(["POST"])
def purchase_request_department_head_approve(
    request: Request, request_id: int
) -> Response:
    """Department head approval."""
    return _workflow_action(
        request, request_id, ApprovePurchaseRequestByDepartmentHead
    )


@api_view(["GET"])
def budget_codes_list(request: Request) -> Response:
    """
    List the AccountChart rows Accounts may assign as a budget code (F25).

    Accounts-only (accounts_verify). Procurement-scoped rather than reusing
    /api/v2/accounts/*, which ordinary Accountants are not granted and whose
    serializers do not expose external_account_type.
    """
    use_case = ListAssignableBudgetCodes(_budget_code_repository, _policy)
    try:
        results = use_case.execute(actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(BudgetCodeSerializer(results, many=True).data)


@api_view(["PUT"])
def purchase_request_item_budget_code(
    request: Request, request_id: int, item_id: int
) -> Response:
    """Accounts assigns one item's budget code while the request is PENDING_ACCOUNTS."""
    serializer = AssignBudgetCodeInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    use_case = AssignItemBudgetCode(_repository, _policy, _budget_code_repository)
    try:
        result = use_case.execute(
            request_id,
            item_id,
            serializer.validated_data["budget_code_id"],
            actor_from_request(request),
        )
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request))


@api_view(["POST"])
def purchase_request_accounts_verify(request: Request, request_id: int) -> Response:
    """Accounts verification."""
    return _workflow_action(request, request_id, VerifyPurchaseRequestByAccounts)


@api_view(["POST"])
def purchase_request_gm_recommend(request: Request, request_id: int) -> Response:
    """General Manager recommendation."""
    return _workflow_action(request, request_id, RecommendPurchaseRequestByGM)


@api_view(["POST"])
def purchase_request_director_approve(request: Request, request_id: int) -> Response:
    """
    Director approval.

    Deliberately does not create a Purchase Order; that integration is out of
    scope for this slice.
    """
    return _workflow_action(request, request_id, ApprovePurchaseRequestByDirector)


@api_view(["POST"])
def purchase_request_process(request: Request, request_id: int) -> Response:
    """
    Procurement processing, the final workflow step (F23).

    Unlike the other workflow transitions this one takes a body: a manually
    entered purchase_order_number. Not routed through _workflow_action since
    that helper is only for no-payload transitions.
    """
    serializer = ProcessPurchaseRequestInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    use_case = ProcessPurchaseRequestByProcurement(_repository, _policy)
    try:
        result = use_case.execute(
            request_id,
            actor_from_request(request),
            purchase_order_number=serializer.validated_data["purchase_order_number"],
        )
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request))


@api_view(["POST"])
def purchase_request_correct_and_resubmit(
    request: Request, request_id: int
) -> Response:
    """
    Correct a rejected request and return it to DRAFT for resubmission.

    One endpoint because the aggregate performs correction and resubmission as
    a single transition.
    """
    return _workflow_action(request, request_id, CorrectAndResubmitPurchaseRequest)


@api_view(["POST"])
def purchase_request_reject(request: Request, request_id: int) -> Response:
    """Reject a purchase request at its current stage."""
    serializer = RejectPurchaseRequestInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    use_case = RejectPurchaseRequest(_repository, _policy)
    try:
        result = use_case.execute(
            request_id,
            actor_from_request(request),
            reason=serializer.validated_data["reason"],
        )
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(_serialize_request(result, request))

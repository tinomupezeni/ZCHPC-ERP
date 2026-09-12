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

from shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainException,
    NotFoundError,
    ValidationError,
)

from modules.procurement.api.actors import actor_from_request, requester_identity
from modules.procurement.api.purchase_request_serializers import (
    CreatePurchaseRequestInputSerializer,
    ListPurchaseRequestsQuerySerializer,
    PurchaseRequestListSerializer,
    PurchaseRequestSerializer,
    RejectPurchaseRequestInputSerializer,
)
from modules.procurement.application.use_cases import (
    ApprovePurchaseRequestByDepartmentHead,
    ApprovePurchaseRequestByDirector,
    CorrectAndResubmitPurchaseRequest,
    CreatePurchaseRequest,
    CreatePurchaseRequestDTO,
    ListPurchaseRequests,
    ProcessPurchaseRequestByProcurement,
    PurchaseRequestItemDTO,
    RecommendPurchaseRequestByGM,
    RejectPurchaseRequest,
    SubmitPurchaseRequest,
    VerifyPurchaseRequestByAccounts,
    ViewPurchaseRequest,
)
from modules.procurement.application.authorization import (
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from modules.procurement.infrastructure.persistence.django_purchase_request_repository import (
    DjangoPurchaseRequestRepository,
)

# Composition root for the purchase request slice.
_repository = DjangoPurchaseRequestRepository()
_directory = DjangoOrganizationalDirectory()
_policy = PurchaseRequestAuthorizationPolicy(directory=_directory)


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


def _workflow_action(request: Request, request_id: int, use_case_cls) -> Response:
    """Run a no-payload workflow transition and return the updated request."""
    use_case = use_case_cls(_repository, _policy)
    try:
        result = use_case.execute(request_id, actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(PurchaseRequestSerializer(result).data)


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
                budget_code_id=item["budget_code_id"],
            )
            for item in serializer.validated_data["items"]
        ],
    )

    try:
        result = CreatePurchaseRequest(_repository, _policy).execute(dto, actor)
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(
        PurchaseRequestSerializer(result).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def purchase_request_detail(request: Request, request_id: int) -> Response:
    """Retrieve a single purchase request."""
    use_case = ViewPurchaseRequest(_repository, _policy)
    try:
        result = use_case.execute(request_id, actor_from_request(request))
    except DomainException as exc:
        return _handle_domain_error(exc)

    return Response(PurchaseRequestSerializer(result).data)


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
    """Procurement processing, the final workflow step."""
    return _workflow_action(request, request_id, ProcessPurchaseRequestByProcurement)


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

    return Response(PurchaseRequestSerializer(result).data)

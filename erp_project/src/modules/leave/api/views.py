"""
Leave API views.
"""

from datetime import date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import DomainException

from modules.leave.api.actors import leave_actor_from_request
from modules.leave.api.errors import error_response
from modules.leave.api.serializers import (
    AdjustLeaveBalanceRequestSerializer,
    AdminLeaveRequestResponseSerializer,
    CreateLeaveTypeRequestSerializer,
    LeaveBalanceQuerySerializer,
    LeaveBalanceResponseSerializer,
    LeaveBalanceSummaryResponseSerializer,
    LeaveRequestQuerySerializer,
    LeaveRequestResponseSerializer,
    LeaveRequestSummaryResponseSerializer,
    LeaveTypeResponseSerializer,
    ReviewLeaveRequestSerializer,
    SetLeaveEntitlementRequestSerializer,
    SubmitLeaveRequestSerializer,
    UpdateLeaveTypeRequestSerializer,
)
from modules.leave.application.services import (
    LeaveBalanceService,
    LeaveRequestService,
    LeaveTypeService,
)
from modules.leave.application.services.leave_balance_service import (
    AdjustLeaveBalanceCommand,
    SetLeaveEntitlementCommand,
)
from modules.leave.application.services.leave_request_service import (
    CancelLeaveRequestCommand,
    ReviewLeaveRequestCommand,
    SubmitLeaveRequestCommand,
)
from modules.leave.application.services.leave_request_query_service import (
    LeaveRequestQueryService,
)
from modules.leave.application.services.leave_type_service import (
    CreateLeaveTypeCommand,
    UpdateLeaveTypeCommand,
)
from modules.leave.domain.services import (
    DefaultLeaveApprovalPolicy,
    LeaveBalanceCalculator,
    LeaveConflictDetector,
)
from modules.leave.domain.value_objects import LeaveStatus
from modules.leave.infrastructure.persistence.django_leave_balance_repository import DjangoLeaveBalanceRepository
from modules.leave.infrastructure.persistence.django_leave_request_repository import DjangoLeaveRequestRepository
from modules.leave.infrastructure.persistence.django_leave_type_repository import DjangoLeaveTypeRepository


def get_leave_type_service() -> LeaveTypeService:
    """Factory for LeaveTypeService."""
    return LeaveTypeService(
        leave_type_repository=DjangoLeaveTypeRepository(),
    )


def get_leave_balance_service() -> LeaveBalanceService:
    """Factory for LeaveBalanceService."""
    return LeaveBalanceService(
        balance_repository=DjangoLeaveBalanceRepository(),
        leave_type_repository=DjangoLeaveTypeRepository(),
        request_repository=DjangoLeaveRequestRepository(),
        balance_calculator=LeaveBalanceCalculator(),
    )


def get_leave_request_service() -> LeaveRequestService:
    """Factory for LeaveRequestService."""
    return LeaveRequestService(
        request_repository=DjangoLeaveRequestRepository(),
        balance_repository=DjangoLeaveBalanceRepository(),
        leave_type_repository=DjangoLeaveTypeRepository(),
        conflict_detector=LeaveConflictDetector(),
        balance_calculator=LeaveBalanceCalculator(),
        approval_policy=DefaultLeaveApprovalPolicy(),
    )


# Authorization (REM-03) is enforced in the leave application services, which
# take the LeaveActor built here. Views only translate HTTP; every service call
# catches DomainException through error_response *before* any broader handler,
# so an AuthorizationError is never reported as a 400.

_NOT_LINKED = {"error": "User is not linked to an employee record"}


# =============================================================================
# Leave Type Views
# =============================================================================


class LeaveTypeListView(APIView):
    """List and create leave types."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all leave types."""
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"
        service = get_leave_type_service()
        leave_types = service.get_all_leave_types(include_inactive=include_inactive)

        return Response(
            [LeaveTypeResponseSerializer(lt).data for lt in leave_types],
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new leave type."""
        serializer = CreateLeaveTypeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_leave_type_service()
        try:
            command = CreateLeaveTypeCommand(**serializer.validated_data)
            leave_type = service.create_leave_type(command, leave_actor_from_request(request))
            return Response(
                LeaveTypeResponseSerializer(leave_type).data,
                status=status.HTTP_201_CREATED,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LeaveTypeDetailView(APIView):
    """Retrieve, update, and delete leave types."""

    permission_classes = [IsAuthenticated]

    def get(self, request, leave_type_id: int):
        """Get a specific leave type."""
        service = get_leave_type_service()
        try:
            leave_type = service.get_leave_type(leave_type_id)
            return Response(
                LeaveTypeResponseSerializer(leave_type).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, leave_type_id: int):
        """Update a leave type."""
        serializer = UpdateLeaveTypeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_leave_type_service()
        try:
            command = UpdateLeaveTypeCommand(
                leave_type_id=leave_type_id,
                **serializer.validated_data,
            )
            leave_type = service.update_leave_type(command, leave_actor_from_request(request))
            return Response(
                LeaveTypeResponseSerializer(leave_type).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, leave_type_id: int):
        """Delete a leave type."""
        service = get_leave_type_service()
        try:
            service.delete_leave_type(leave_type_id, leave_actor_from_request(request))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# Leave Balance Views
# =============================================================================


class LeaveBalanceListView(APIView):
    """Get leave balances for current employee."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all leave balances for current employee."""
        actor = leave_actor_from_request(request)
        employee_id = actor.employee_id
        if not employee_id:
            return Response(_NOT_LINKED, status=status.HTTP_400_BAD_REQUEST)

        query_serializer = LeaveBalanceQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        year = query_serializer.validated_data.get("year", date.today().year)

        service = get_leave_balance_service()
        try:
            summary = service.get_all_balances(employee_id=employee_id, year=year, actor=actor)
        except DomainException as e:
            return error_response(e)

        return Response(
            LeaveBalanceSummaryResponseSerializer(summary).data,
            status=status.HTTP_200_OK,
        )


class LeaveBalanceDetailView(APIView):
    """Get or adjust a specific leave balance."""

    permission_classes = [IsAuthenticated]

    def get(self, request, balance_id: int):
        """Get a specific leave balance (own, or any with balance view_any)."""
        service = get_leave_balance_service()
        try:
            dto = service.get_balance_by_id(balance_id, leave_actor_from_request(request))
        except DomainException as e:
            return error_response(e)
        return Response(
            LeaveBalanceResponseSerializer(dto).data,
            status=status.HTTP_200_OK,
        )


class LeaveBalanceAdminView(APIView):
    """Admin view for managing leave balances."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Set leave entitlement for an employee."""
        serializer = SetLeaveEntitlementRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_leave_balance_service()
        try:
            command = SetLeaveEntitlementCommand(**serializer.validated_data)
            balance = service.create_or_update_balance(command, leave_actor_from_request(request))
            return Response(
                LeaveBalanceResponseSerializer(balance).data,
                status=status.HTTP_201_CREATED,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LeaveBalanceAdjustView(APIView):
    """Adjust a specific leave balance."""

    permission_classes = [IsAuthenticated]

    def post(self, request, balance_id: int):
        """Adjust leave balance."""
        serializer = AdjustLeaveBalanceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor = leave_actor_from_request(request)
        service = get_leave_balance_service()
        try:
            command = AdjustLeaveBalanceCommand(
                balance_id=balance_id,
                adjusted_by_id=actor.employee_id,
                **serializer.validated_data,
            )
            balance = service.adjust_balance(command, actor)
            return Response(
                LeaveBalanceResponseSerializer(balance).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InitializeBalancesView(APIView):
    """Initialize leave balances for an employee."""

    permission_classes = [IsAuthenticated]

    def post(self, request, employee_id: int):
        """Initialize leave balances using default days."""
        year = request.data.get("year", date.today().year)

        service = get_leave_balance_service()
        try:
            balances = service.initialize_balances_for_employee(
                employee_id=employee_id,
                year=year,
                actor=leave_actor_from_request(request),
            )
            return Response(
                [LeaveBalanceResponseSerializer(b).data for b in balances],
                status=status.HTTP_201_CREATED,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# Leave Request Views
# =============================================================================


class LeaveRequestListView(APIView):
    """List and create leave requests for current employee."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get leave requests for current employee."""
        actor = leave_actor_from_request(request)
        employee_id = actor.employee_id
        if not employee_id:
            return Response(_NOT_LINKED, status=status.HTTP_400_BAD_REQUEST)

        query_serializer = LeaveRequestQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        year = query_serializer.validated_data.get("year")
        status_str = query_serializer.validated_data.get("status")
        leave_status = None
        if status_str:
            status_map = {
                "Pending": LeaveStatus.PENDING,
                "Approved": LeaveStatus.APPROVED,
                "Rejected": LeaveStatus.REJECTED,
                "Cancelled": LeaveStatus.CANCELLED,
            }
            leave_status = status_map.get(status_str)

        service = get_leave_request_service()
        try:
            requests = service.get_employee_requests(
                employee_id=employee_id,
                actor=actor,
                year=year,
                status=leave_status,
            )
        except DomainException as e:
            return error_response(e)

        return Response(
            [LeaveRequestResponseSerializer(r).data for r in requests],
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Submit a new leave request."""
        actor = leave_actor_from_request(request)
        employee_id = actor.employee_id
        if not employee_id:
            return Response(_NOT_LINKED, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmitLeaveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_leave_request_service()
        try:
            command = SubmitLeaveRequestCommand(
                employee_id=employee_id,
                **serializer.validated_data,
            )
            leave_request = service.submit_leave_request(command, actor)
            return Response(
                LeaveRequestResponseSerializer(leave_request).data,
                status=status.HTTP_201_CREATED,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AdminLeaveRequestListView(APIView):
    """
    Leave requests across employees - what the HR "Leave Applications" admin
    page needs.

    Every request for an actor holding leave.request.view_any; otherwise only
    the actor's own (REM-03 - this replaced a role-name check).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List leave requests visible to the actor, most recently requested first."""
        try:
            requests = LeaveRequestQueryService().list_requests(leave_actor_from_request(request))
        except DomainException as e:
            return error_response(e)

        return Response(
            AdminLeaveRequestResponseSerializer(requests, many=True).data,
            status=status.HTTP_200_OK,
        )


class LeaveRequestDetailView(APIView):
    """Retrieve a specific leave request."""

    permission_classes = [IsAuthenticated]

    def get(self, request, request_id: int):
        """Get a specific leave request."""
        service = get_leave_request_service()
        try:
            leave_request = service.get_leave_request(request_id, leave_actor_from_request(request))
            return Response(
                LeaveRequestResponseSerializer(leave_request).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e, default_status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class LeaveRequestCancelView(APIView):
    """Cancel a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id: int):
        """Cancel a leave request."""
        service = get_leave_request_service()
        try:
            command = CancelLeaveRequestCommand(request_id=request_id)
            leave_request = service.cancel_leave_request(command, leave_actor_from_request(request))
            return Response(
                LeaveRequestResponseSerializer(leave_request).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LeaveRequestReviewView(APIView):
    """Review (approve/reject) a leave request."""

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id: int):
        """Review a leave request."""
        # Review authority is leave.request.review alone (confirmed REM-03
        # decision); the service enforces it. An unlinked superuser may still
        # review (reviewer_id None); an unlinked non-superuser resolves to no
        # permissions and is refused there.
        actor = leave_actor_from_request(request)

        serializer = ReviewLeaveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_leave_request_service()
        try:
            command = ReviewLeaveRequestCommand(
                request_id=request_id,
                reviewer_id=actor.employee_id,
                **serializer.validated_data,
            )

            if command.approved:
                leave_request = service.approve_leave_request(command, actor)
            else:
                leave_request = service.reject_leave_request(command, actor)

            return Response(
                LeaveRequestResponseSerializer(leave_request).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PendingLeaveRequestsView(APIView):
    """
    Pending leave requests: the review queue for a holder of
    leave.request.review, otherwise only the actor's own pending requests.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get pending leave requests visible to the actor."""
        service = get_leave_request_service()
        try:
            pending_requests = service.get_pending_requests(leave_actor_from_request(request))
        except DomainException as e:
            return error_response(e)

        return Response(
            [LeaveRequestResponseSerializer(r).data for r in pending_requests],
            status=status.HTTP_200_OK,
        )


class LeaveRequestSummaryView(APIView):
    """Get leave request summary for current employee."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get leave request summary."""
        actor = leave_actor_from_request(request)
        employee_id = actor.employee_id
        if not employee_id:
            return Response(_NOT_LINKED, status=status.HTTP_400_BAD_REQUEST)

        year = int(request.query_params.get("year", date.today().year))

        service = get_leave_request_service()
        try:
            summary = service.get_request_summary(employee_id=employee_id, year=year, actor=actor)
        except DomainException as e:
            return error_response(e)

        return Response(
            LeaveRequestSummaryResponseSerializer(summary).data,
            status=status.HTTP_200_OK,
        )

"""
API views for the portal module.
"""

from datetime import date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from modules.procurement.infrastructure.persistence.models import FuelRequisition, StoresRequisition, ComparativeSchedule

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.portal.application.services import (
    PortalAuthService,
    DashboardService,
    PortalAttendanceService,
    PortalLeaveService,
    PortalPayslipService,
    CareersService,
)
from modules.portal.infrastructure.persistence.django_providers import (
    DjangoEmployeeProvider,
    DjangoAttendanceProvider,
    DjangoLeaveProvider,
    DjangoPayrollProvider,
    DjangoRecruitmentProvider,
    DjangoEventProvider,
)
from modules.portal.infrastructure.persistence.django_repositories import (
    DjangoNotificationRepository,
    DjangoQRTokenRepository,
)
from modules.portal.api.serializers import (
    LoginSerializer,
    EmployeeProfileSerializer,
    DashboardSerializer,
    ClockStatusSerializer,
    QRClockSerializer,
    AttendanceRecordSerializer,
    AttendanceSummarySerializer,
    LeaveBalanceSerializer,
    LeaveRequestSerializer,
    CreateLeaveRequestSerializer,
    PayslipSerializer,
    JobListingSerializer,
    JobDetailSerializer,
    JobApplicationSerializer,
    ApplicationStatusSerializer,
    NotificationSerializer,
    FuelRequisitionSerializer,
    CreateFuelRequisitionSerializer,
    StoresRequisitionSerializer,
    CreateStoresRequisitionSerializer,
    ComparativeScheduleSerializer,
    CreateComparativeScheduleSerializer,
)


# Initialize providers and repositories
_employee_provider = DjangoEmployeeProvider()
_attendance_provider = DjangoAttendanceProvider()
_leave_provider = DjangoLeaveProvider()
_payroll_provider = DjangoPayrollProvider()
_recruitment_provider = DjangoRecruitmentProvider()
_event_provider = DjangoEventProvider()
_notification_repo = DjangoNotificationRepository()
_qr_token_repo = DjangoQRTokenRepository()

# Initialize services
_auth_service = PortalAuthService(_employee_provider)
_dashboard_service = DashboardService(
    _employee_provider,
    _attendance_provider,
    _leave_provider,
    _event_provider,
    _notification_repo,
)
_attendance_service = PortalAttendanceService(
    _attendance_provider,
    _qr_token_repo,
)
_leave_service = PortalLeaveService(
    _leave_provider,
    _notification_repo,
)
_payslip_service = PortalPayslipService(_payroll_provider)
_careers_service = CareersService(_recruitment_provider)


def _get_employee_id(request: Request) -> int:
    """Get employee ID from authenticated user."""
    employee = _employee_provider.get_by_user_id(request.user.id)
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee.id


# ============================
# Authentication Views
# ============================

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request: Request) -> Response:
    """Login with EC number and password."""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    result = _auth_service.authenticate(
        ec_number=serializer.validated_data["ec_number"],
        password=serializer.validated_data["password"],
    )

    if not result.success:
        return Response(
            {"error": result.message},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT tokens
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(pk=result.employee.user_id)
    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "employee": EmployeeProfileSerializer(result.employee).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request: Request) -> Response:
    """Logout and blacklist refresh token."""
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Logged out successfully"})
    except Exception:
        return Response(
            {"error": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    """Get current employee profile."""
    try:
        employee = _auth_service.get_current_employee(request.user.id)
        return Response(EmployeeProfileSerializer(employee).data)
    except NotFoundError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


# ============================
# Dashboard Views
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request: Request) -> Response:
    """Get dashboard data."""
    try:
        employee_id = _get_employee_id(request)
        data = _dashboard_service.get_dashboard(employee_id)
        return Response(DashboardSerializer(data).data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================
# Attendance Views
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attendance_status(request: Request) -> Response:
    """Get today's attendance status."""
    employee_id = _get_employee_id(request)
    clock_status = _attendance_service.get_today_status(employee_id)
    return Response(ClockStatusSerializer(clock_status).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attendance_clock(request: Request) -> Response:
    """Clock in or out."""
    employee_id = _get_employee_id(request)
    clock_status = _attendance_service.get_today_status(employee_id)

    if clock_status.is_clocked_in:
        result = _attendance_service.clock_out(employee_id)
    else:
        result = _attendance_service.clock_in(employee_id)

    if not result.success:
        return Response(
            {"error": result.message},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": result.message,
        "record": AttendanceRecordSerializer(result.record).data,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def attendance_qr_token(request: Request) -> Response:
    """Get current QR token for display."""
    token = _attendance_service.get_current_qr_token()
    return Response({"token": token})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attendance_qr_clock(request: Request) -> Response:
    """Clock in/out using QR token."""
    serializer = QRClockSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    employee_id = _get_employee_id(request)
    result = _attendance_service.clock_with_qr(
        employee_id=employee_id,
        token=serializer.validated_data["token"],
    )

    if not result.success:
        return Response(
            {"error": result.message},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": result.message,
        "record": AttendanceRecordSerializer(result.record).data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attendance_history(request: Request) -> Response:
    """Get attendance history."""
    employee_id = _get_employee_id(request)

    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    records = _attendance_service.get_attendance_history(
        employee_id=employee_id,
        from_date=date.fromisoformat(from_date) if from_date else None,
        to_date=date.fromisoformat(to_date) if to_date else None,
    )

    return Response(AttendanceRecordSerializer(records, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def attendance_summary(request: Request) -> Response:
    """Get monthly attendance summary."""
    employee_id = _get_employee_id(request)

    year = request.query_params.get("year")
    month = request.query_params.get("month")

    summary = _attendance_service.get_monthly_summary(
        employee_id=employee_id,
        year=int(year) if year else None,
        month=int(month) if month else None,
    )

    return Response(AttendanceSummarySerializer(summary).data)


# ============================
# Leave Views
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leave_balances(request: Request) -> Response:
    """Get leave balances."""
    employee_id = _get_employee_id(request)
    year = request.query_params.get("year")

    balances = _leave_service.get_balances(
        employee_id=employee_id,
        year=int(year) if year else None,
    )

    return Response(LeaveBalanceSerializer(balances, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def leave_requests(request: Request) -> Response:
    """List or create leave requests."""
    employee_id = _get_employee_id(request)

    if request.method == "GET":
        status_filter = request.query_params.get("status")
        requests = _leave_service.get_requests(
            employee_id=employee_id,
            status=status_filter,
        )
        return Response(LeaveRequestSerializer(requests, many=True).data)

    elif request.method == "POST":
        serializer = CreateLeaveRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = _leave_service.create_request(
            employee_id=employee_id,
            **serializer.validated_data,
        )

        if not result.success:
            return Response(
                {"error": result.message},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            LeaveRequestSerializer(result.request).data,
            status=status.HTTP_201_CREATED
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def leave_request_cancel(request: Request, request_id: int) -> Response:
    """Cancel a leave request."""
    employee_id = _get_employee_id(request)

    result = _leave_service.cancel_request(
        employee_id=employee_id,
        request_id=request_id,
    )

    if not result.success:
        return Response(
            {"error": result.message},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({"message": result.message})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leave_summary(request: Request) -> Response:
    """Get leave summary."""
    employee_id = _get_employee_id(request)
    summary = _leave_service.get_summary(employee_id)
    return Response(summary)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def fuel_requisitions(request: Request) -> Response:
    """List or submit fuel requisitions for the authenticated employee."""
    from modules.hr.infrastructure.persistence.models import Employees

    try:
        employee = Employees.objects.get(user_id=request.user.id)
    except Employees.DoesNotExist:
        return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    if not employee.department_id:
        return Response({"error": "Employee department is required"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        records = FuelRequisition.objects.filter(requester=request.user).select_related("department")
        return Response(FuelRequisitionSerializer(records, many=True).data)

    serializer = CreateFuelRequisitionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    if data["diesel_quantity"] == 0 and data["petrol_quantity"] == 0:
        return Response({"error": "Enter a diesel or petrol quantity"}, status=status.HTTP_400_BAD_REQUEST)
    record = FuelRequisition.objects.create(
        requester=request.user,
        department_id=employee.department_id,
        **data,
    )
    return Response(FuelRequisitionSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def stores_requisitions(request: Request) -> Response:
    """List or submit Stores Requisition forms for the authenticated employee."""
    from modules.hr.infrastructure.persistence.models import Employees

    try:
        employee = Employees.objects.get(user_id=request.user.id)
    except Employees.DoesNotExist:
        return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    if not employee.department_id:
        return Response({"error": "Employee department is required"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        records = StoresRequisition.objects.filter(requester=request.user).select_related("department")
        return Response(StoresRequisitionSerializer(records, many=True).data)

    serializer = CreateStoresRequisitionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    record = StoresRequisition.objects.create(
        requester=request.user,
        department_id=employee.department_id,
        items=serializer.validated_data["items"],
    )
    return Response(StoresRequisitionSerializer(record).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def comparative_schedules(request: Request) -> Response:
    """List or submit quotation comparison schedules."""
    if request.method == "GET":
        records = ComparativeSchedule.objects.filter(requester=request.user)
        return Response(ComparativeScheduleSerializer(records, many=True).data)
    serializer = CreateComparativeScheduleSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    record = ComparativeSchedule.objects.create(requester=request.user, **serializer.validated_data)
    return Response(ComparativeScheduleSerializer(record).data, status=status.HTTP_201_CREATED)


# ============================
# Payslip Views
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payslips(request: Request) -> Response:
    """List payslips."""
    employee_id = _get_employee_id(request)
    year = request.query_params.get("year")

    payslip_list = _payslip_service.get_payslips(
        employee_id=employee_id,
        year=int(year) if year else None,
    )

    return Response(PayslipSerializer(payslip_list, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payslip_detail(request: Request, payslip_id: int) -> Response:
    """Get payslip detail."""
    employee_id = _get_employee_id(request)

    breakdown = _payslip_service.get_payslip_breakdown(
        employee_id=employee_id,
        payslip_id=payslip_id,
    )

    if breakdown is None:
        return Response(
            {"error": "Payslip not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(breakdown)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payslip_summary(request: Request) -> Response:
    """Get yearly payslip summary."""
    employee_id = _get_employee_id(request)
    year = request.query_params.get("year")

    summary = _payslip_service.get_yearly_summary(
        employee_id=employee_id,
        year=int(year) if year else None,
    )

    return Response(summary)


# ============================
# Public Careers Views
# ============================

@api_view(["GET"])
@permission_classes([AllowAny])
def public_jobs(request: Request) -> Response:
    """List open jobs (public)."""
    jobs = _careers_service.get_open_jobs()
    return Response(JobListingSerializer(jobs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def public_job_detail(request: Request, job_id: int) -> Response:
    """Get job details (public)."""
    job = _careers_service.get_job(job_id)

    if job is None:
        return Response(
            {"error": "Job not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(JobDetailSerializer(job).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def public_job_apply(request: Request, job_id: int) -> Response:
    """Apply for a job (public)."""
    serializer = JobApplicationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    result = _careers_service.apply_for_job(
        job_id=job_id,
        candidate_data=serializer.validated_data,
    )

    if not result.success:
        return Response(
            {"error": result.message},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": result.message,
        "application_id": result.application_id,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def public_application_status(request: Request) -> Response:
    """Check application status by national ID (public)."""
    national_id = request.data.get("national_id")

    if not national_id:
        return Response(
            {"error": "National ID is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    applications = _careers_service.check_application_status(national_id)
    return Response(ApplicationStatusSerializer(applications, many=True).data)


# ============================
# Notification Views
# ============================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications(request: Request) -> Response:
    """List notifications."""
    employee_id = _get_employee_id(request)

    is_read = request.query_params.get("is_read")
    if is_read is not None:
        is_read = is_read.lower() == "true"

    notification_list = _notification_repo.get_by_employee(
        employee_id=employee_id,
        is_read=is_read,
    )

    return Response(NotificationSerializer(notification_list, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_unread_count(request: Request) -> Response:
    """Get unread notification count."""
    employee_id = _get_employee_id(request)
    count = _notification_repo.get_unread_count(employee_id)
    return Response({"unread_count": count})


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def notification_mark_read(request: Request, notification_id: int) -> Response:
    """Mark notification as read."""
    notification = _notification_repo.get_by_id(notification_id)

    if notification is None:
        return Response(
            {"error": "Notification not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    notification.mark_as_read()
    _notification_repo.save(notification)

    return Response(NotificationSerializer(notification).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notifications_mark_all_read(request: Request) -> Response:
    """Mark all notifications as read."""
    employee_id = _get_employee_id(request)
    count = _notification_repo.mark_all_read(employee_id)
    return Response({"marked_read": count})

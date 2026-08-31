"""
Attendance API views.
"""

from calendar import monthrange
from datetime import date

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.attendance.api.serializers import (
    AdminAttendanceListResponseSerializer,
    AdminAttendanceQuerySerializer,
    AdminAttendanceRecordResponseSerializer,
    AttendanceHistoryQuerySerializer,
    AttendanceHistoryResponseSerializer,
    AttendanceRecordResponseSerializer,
    AttendanceSummaryQuerySerializer,
    AttendanceSummaryResponseSerializer,
    ClockInRequestSerializer,
    ClockOutRequestSerializer,
    ClockResponseSerializer,
    QRClockInRequestSerializer,
    QRClockInResponseSerializer,
    QRTokenResponseSerializer,
    UpdateAttendanceRequestSerializer,
)
from modules.attendance.application.services import (
    AttendanceService,
    ClockInCommand,
    ClockOutCommand,
    QRTokenService,
    UpdateAttendanceCommand,
    VerifyTokenCommand,
)
from modules.attendance.infrastructure.persistence.attendance_repository import DjangoAttendanceRepository
from modules.attendance.infrastructure.persistence.qr_token_repository import DjangoQRTokenRepository
from modules.identity.infrastructure.permissions import IsHRorAdmin


def get_attendance_service() -> AttendanceService:
    """Factory for AttendanceService."""
    return AttendanceService(
        attendance_repo=DjangoAttendanceRepository(),
    )


def get_qr_token_service() -> QRTokenService:
    """Factory for QRTokenService."""
    return QRTokenService(
        token_repo=DjangoQRTokenRepository(),
    )


class ClockInView(APIView):
    """Clock-in endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Clock in the current user."""
        serializer = ClockInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get employee ID from user
        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                {"error": "User is not linked to an employee record"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = get_attendance_service()

        try:
            command = ClockInCommand(
                employee_id=employee_id,
                clock_time=serializer.validated_data.get("clock_time"),
            )
            record = service.clock_in(command)
            record_dto = service.get_today_status(employee_id)

            response_data = {
                "action": "clock_in",
                "message": "Successfully clocked in",
                "record": AttendanceRecordResponseSerializer(record_dto).data,
            }
            return Response(
                ClockResponseSerializer(response_data).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None


class ClockOutView(APIView):
    """Clock-out endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Clock out the current user."""
        serializer = ClockOutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                {"error": "User is not linked to an employee record"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = get_attendance_service()

        try:
            command = ClockOutCommand(
                employee_id=employee_id,
                clock_time=serializer.validated_data.get("clock_time"),
            )
            record = service.clock_out(command)
            record_dto = service.get_today_status(employee_id)

            response_data = {
                "action": "clock_out",
                "message": f"Successfully clocked out. Hours worked: {record_dto.hours_worked:.2f}",
                "record": AttendanceRecordResponseSerializer(record_dto).data,
            }
            return Response(
                ClockResponseSerializer(response_data).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None


class AttendanceStatusView(APIView):
    """Today's attendance status endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get today's attendance status."""
        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                {"error": "User is not linked to an employee record"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = get_attendance_service()
        record_dto = service.get_today_status(employee_id)

        if not record_dto:
            return Response(
                {
                    "clocked_in": False,
                    "clocked_out": False,
                    "record": None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "clocked_in": record_dto.time_in is not None,
                "clocked_out": record_dto.time_out is not None,
                "record": AttendanceRecordResponseSerializer(record_dto).data,
            },
            status=status.HTTP_200_OK,
        )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None


class AttendanceHistoryView(APIView):
    """Attendance history endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get attendance history for current user."""
        query_serializer = AttendanceHistoryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                {"error": "User is not linked to an employee record"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Default to current month
        today = date.today()
        start_date = query_serializer.validated_data.get(
            "start_date", today.replace(day=1)
        )
        end_date = query_serializer.validated_data.get(
            "end_date",
            today.replace(day=monthrange(today.year, today.month)[1]),
        )
        page = query_serializer.validated_data.get("page", 1)
        page_size = query_serializer.validated_data.get("page_size", 20)

        service = get_attendance_service()
        all_records = service.get_history(employee_id, start_date, end_date)

        # Paginate
        total = len(all_records)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        records = all_records[start_idx:end_idx]

        response_data = {
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "results": [AttendanceRecordResponseSerializer(r).data for r in records],
        }

        return Response(
            AttendanceHistoryResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None


class AttendanceSummaryView(APIView):
    """Attendance summary endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get attendance summary for current user."""
        query_serializer = AttendanceSummaryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                {"error": "User is not linked to an employee record"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Default to current month
        today = date.today()
        year = query_serializer.validated_data.get("year", today.year)
        month = query_serializer.validated_data.get("month", today.month)

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        service = get_attendance_service()
        summary = service.get_summary(employee_id, start_date, end_date)

        return Response(
            AttendanceSummaryResponseSerializer(summary).data,
            status=status.HTTP_200_OK,
        )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None


class AdminAttendanceListView(APIView):
    """
    Admin/HR endpoint listing attendance records across employees.

    Supports filtering by department, employee, and date range - unlike
    AttendanceHistoryView, which is scoped to the requesting user only.
    """

    permission_classes = [IsAuthenticated, IsHRorAdmin]

    def get(self, request):
        """List attendance records, optionally filtered."""
        query_serializer = AdminAttendanceQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        service = get_attendance_service()
        all_records = service.get_filtered_history(
            department_id=filters.get("department_id"),
            employee_id=filters.get("employee_id"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        total = len(all_records)
        total_pages = (total + page_size - 1) // page_size if total else 0
        start_idx = (page - 1) * page_size
        page_records = all_records[start_idx : start_idx + page_size]

        employee_info = self._employee_display_info({r.employee_id for r in page_records})

        results = []
        for record in page_records:
            data = AttendanceRecordResponseSerializer(record).data
            info = employee_info.get(record.employee_id, {})
            data["employee_name"] = info.get("name", "Unknown")
            data["department_name"] = info.get("department")
            results.append(data)

        response_data = {
            "count": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "results": results,
        }

        return Response(
            AdminAttendanceListResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )

    def _employee_display_info(self, employee_ids: set) -> dict:
        """Bulk-fetch employee name/department for the given employee IDs."""
        from modules.hr.infrastructure.persistence.models import Employees

        if not employee_ids:
            return {}

        employees = Employees.objects.filter(id__in=employee_ids).select_related("department")

        info = {}
        for employee in employees:
            info[employee.id] = {
                "name": f"{employee.first_name} {employee.surname}".strip(),
                "department": employee.department.name if employee.department else None,
            }
        return info


class QRTokenView(APIView):
    """QR token endpoint for displays."""

    permission_classes = [AllowAny]  # Public endpoint for office displays

    def get(self, request):
        """Get current QR token."""
        service = get_qr_token_service()
        token_dto = service.get_or_create_current_token()

        return Response(
            QRTokenResponseSerializer(token_dto).data,
            status=status.HTTP_200_OK,
        )


class QRClockInView(APIView):
    """QR-based clock-in endpoint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Clock in using scanned QR token."""
        serializer = QRClockInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee_id = self._get_employee_id(request.user)
        if not employee_id:
            return Response(
                QRClockInResponseSerializer({
                    "success": False,
                    "message": "User is not linked to an employee record",
                }).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        qr_service = get_qr_token_service()
        attendance_service = get_attendance_service()

        # Verify token
        verify_command = VerifyTokenCommand(
            token_string=serializer.validated_data["token"],
            employee_id=employee_id,
        )

        if not qr_service.verify_token(verify_command):
            return Response(
                QRClockInResponseSerializer({
                    "success": False,
                    "message": "Invalid or expired QR code. Please scan the current code.",
                }).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform clock in/out
        try:
            # Check current status
            today_status = attendance_service.get_today_status(employee_id)

            if today_status is None or today_status.time_in is None:
                # Clock in
                command = ClockInCommand(employee_id=employee_id)
                attendance_service.clock_in(command)
                record_dto = attendance_service.get_today_status(employee_id)

                return Response(
                    QRClockInResponseSerializer({
                        "success": True,
                        "message": "Successfully clocked in",
                        "action": "clock_in",
                        "record": AttendanceRecordResponseSerializer(record_dto).data,
                    }).data,
                    status=status.HTTP_200_OK,
                )
            elif today_status.time_out is None:
                # Clock out
                command = ClockOutCommand(employee_id=employee_id)
                attendance_service.clock_out(command)
                record_dto = attendance_service.get_today_status(employee_id)

                return Response(
                    QRClockInResponseSerializer({
                        "success": True,
                        "message": f"Successfully clocked out. Hours worked: {record_dto.hours_worked:.2f}",
                        "action": "clock_out",
                        "record": AttendanceRecordResponseSerializer(record_dto).data,
                    }).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    QRClockInResponseSerializer({
                        "success": False,
                        "message": "Already clocked out for today",
                    }).data,
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                QRClockInResponseSerializer({
                    "success": False,
                    "message": str(e),
                }).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_employee_id(self, user) -> int | None:
        """Get employee ID from user."""
        from modules.hr.infrastructure.persistence.models import Employees

        try:
            employee = Employees.objects.get(user=user)
            return employee.id
        except Employees.DoesNotExist:
            return None

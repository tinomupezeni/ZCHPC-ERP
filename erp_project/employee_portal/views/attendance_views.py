from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Avg, Sum, Count
from datetime import timedelta, datetime, time
from decimal import Decimal

from human_resources.hr_models import AttendanceRecord, LeaveRequest
from ..models import AttendanceQRToken
from ..serializers.attendance_serializers import (
    AttendanceRecordSerializer,
    ClockInOutSerializer,
    AttendanceStatusSerializer,
    AttendanceSummarySerializer,
)


class ClockInOutView(APIView):
    """
    Clock in or out for attendance.

    POST /api/portal/attendance/clock/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClockInOutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.localdate()
        now = timezone.localtime()

        # Get or create today's attendance record
        attendance, created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'time_in': now.time()}
        )

        if created:
            # New clock in
            action = 'clock_in'
            message = f'Clocked in at {now.strftime("%H:%M")}'
        elif attendance.time_in and not attendance.time_out:
            # Clock out
            attendance.time_out = now.time()
            attendance.save(update_fields=['time_out'])
            action = 'clock_out'
            message = f'Clocked out at {now.strftime("%H:%M")}'
        elif attendance.time_out:
            # Already clocked out today
            return Response(
                {'detail': 'You have already clocked out today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Clock in (shouldn't normally reach here)
            attendance.time_in = now.time()
            attendance.save(update_fields=['time_in'])
            action = 'clock_in'
            message = f'Clocked in at {now.strftime("%H:%M")}'

        # Calculate hours worked if clocked out
        hours_worked = None
        if attendance.time_in and attendance.time_out:
            clock_in_dt = datetime.combine(today, attendance.time_in)
            clock_out_dt = datetime.combine(today, attendance.time_out)
            hours_worked = (clock_out_dt - clock_in_dt).total_seconds() / 3600

        return Response({
            'action': action,
            'message': message,
            'date': today,
            'clock_in': attendance.time_in,
            'clock_out': attendance.time_out,
            'hours_worked': round(hours_worked, 2) if hours_worked else None,
        })


class AttendanceStatusView(APIView):
    """
    Get today's attendance status.

    GET /api/portal/attendance/status/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.localdate()

        try:
            attendance = AttendanceRecord.objects.get(
                employee=employee,
                date=today
            )
            if attendance.time_out:
                status_str = 'clocked_out'
            elif attendance.time_in:
                status_str = 'clocked_in'
            else:
                status_str = 'not_clocked'

            # Calculate hours worked
            hours_worked = None
            if attendance.time_in and attendance.time_out:
                clock_in_dt = datetime.combine(today, attendance.time_in)
                clock_out_dt = datetime.combine(today, attendance.time_out)
                hours_worked = Decimal(str((clock_out_dt - clock_in_dt).total_seconds() / 3600))

            data = {
                'date': today,
                'clock_in': attendance.time_in,
                'clock_out': attendance.time_out,
                'status': status_str,
                'hours_worked': round(hours_worked, 2) if hours_worked else None,
            }
        except AttendanceRecord.DoesNotExist:
            data = {
                'date': today,
                'clock_in': None,
                'clock_out': None,
                'status': 'not_clocked',
                'hours_worked': None,
            }

        serializer = AttendanceStatusSerializer(data)
        return Response(serializer.data)


class AttendanceHistoryView(APIView):
    """
    Get attendance history with pagination and filters.

    GET /api/portal/attendance/history/
    Query params: start_date, end_date, page, page_size
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 30))

        queryset = AttendanceRecord.objects.filter(employee=employee)

        # Apply date filters
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Default to current month if no filters
        if not start_date and not end_date:
            today = timezone.localdate()
            start_of_month = today.replace(day=1)
            queryset = queryset.filter(date__gte=start_of_month)

        # Order and paginate
        total_count = queryset.count()
        queryset = queryset.order_by('-date')[(page - 1) * page_size:page * page_size]

        serializer = AttendanceRecordSerializer(queryset, many=True)

        return Response({
            'records': serializer.data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
        })


class AttendanceSummaryView(APIView):
    """
    Get monthly attendance summary.

    GET /api/portal/attendance/summary/
    Query params: month, year
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse query params
        today = timezone.localdate()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))

        # Calculate date range for the month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Get attendance records for the month
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=start_date,
            date__lte=end_date
        )

        # Count days
        days_present = records.filter(time_in__isnull=False).count()

        # Get leave days (calculate from start_date and end_date)
        leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            status='Approved',
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        days_on_leave = 0
        for leave in leave_requests:
            # Calculate overlap between leave period and the month
            leave_start = max(leave.start_date, start_date)
            leave_end = min(leave.end_date, end_date)
            days_on_leave += (leave_end - leave_start).days + 1

        # Calculate working days (exclude weekends)
        total_working_days = 0
        current_date = start_date
        while current_date <= min(end_date, today):
            if current_date.weekday() < 5:  # Monday to Friday
                total_working_days += 1
            current_date += timedelta(days=1)

        days_absent = max(0, total_working_days - days_present - days_on_leave)

        # Calculate total hours worked
        total_hours = Decimal('0')
        for record in records:
            if record.time_in and record.time_out:
                clock_in_dt = datetime.combine(record.date, record.time_in)
                clock_out_dt = datetime.combine(record.date, record.time_out)
                hours = Decimal(str((clock_out_dt - clock_in_dt).total_seconds() / 3600))
                total_hours += hours

        # Calculate averages (simplified)
        avg_clock_in = None
        avg_clock_out = None
        records_with_times = records.filter(time_in__isnull=False)
        if records_with_times.exists():
            # For simplicity, just get the most common clock in time
            first_record = records_with_times.first()
            if first_record:
                avg_clock_in = first_record.time_in
                avg_clock_out = first_record.time_out

        data = {
            'month': month,
            'year': year,
            'total_working_days': total_working_days,
            'days_present': days_present,
            'days_absent': days_absent,
            'days_late': 0,  # Would require late threshold configuration
            'days_on_leave': days_on_leave,
            'total_hours_worked': float(round(total_hours, 2)),
            'average_clock_in': avg_clock_in,
            'average_clock_out': avg_clock_out,
        }

        serializer = AttendanceSummarySerializer(data)
        return Response(serializer.data)


class QRTokenView(APIView):
    """
    Get the current QR token for display.
    This endpoint should be accessed by an office display/tablet.

    GET /api/portal/attendance/qr/token/
    """
    # Allow any - the QR display doesn't need auth, but it's secured by:
    # 1. The token itself rotates every 30 seconds
    # 2. Only someone physically present can scan the code
    permission_classes = [AllowAny]

    def get(self, request):
        # Get or create current valid token
        token = AttendanceQRToken.get_or_create_current_token(validity_seconds=30)

        # Calculate time remaining
        now = timezone.now()
        time_remaining = (token.expires_at - now).total_seconds()

        return Response({
            'token': token.token,
            'expires_at': token.expires_at,
            'time_remaining': max(0, int(time_remaining)),
            'validity_seconds': 30,
        })


class QRClockInView(APIView):
    """
    Clock in by scanning QR code.
    Employee must be authenticated and scan a valid QR token.

    POST /api/portal/attendance/qr/clock-in/
    Body: { "token": "scanned_qr_token" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the token from request
        scanned_token = request.data.get('token')
        if not scanned_token:
            return Response(
                {'detail': 'QR token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the token
        token = AttendanceQRToken.verify_token(scanned_token)
        if not token:
            return Response(
                {'detail': 'Invalid or expired QR code. Please scan the current code displayed at the office.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.localdate()
        now = timezone.localtime()

        # Check if already clocked in today
        existing_record = AttendanceRecord.objects.filter(
            employee=employee,
            date=today
        ).first()

        if existing_record:
            if existing_record.time_out:
                return Response(
                    {'detail': 'You have already clocked out today'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing_record.time_in:
                # Already clocked in, this is a clock out
                existing_record.time_out = now.time()
                existing_record.save(update_fields=['time_out'])

                # Increment token usage
                token.increment_usage()

                # Calculate hours worked
                clock_in_dt = datetime.combine(today, existing_record.time_in)
                clock_out_dt = datetime.combine(today, existing_record.time_out)
                hours_worked = (clock_out_dt - clock_in_dt).total_seconds() / 3600

                return Response({
                    'action': 'clock_out',
                    'message': f'Successfully clocked out at {now.strftime("%H:%M")}',
                    'date': today,
                    'clock_in': existing_record.time_in,
                    'clock_out': existing_record.time_out,
                    'hours_worked': round(hours_worked, 2),
                })

        # Create new clock in record
        attendance = AttendanceRecord.objects.create(
            employee=employee,
            date=today,
            time_in=now.time()
        )

        # Increment token usage
        token.increment_usage()

        return Response({
            'action': 'clock_in',
            'message': f'Successfully clocked in at {now.strftime("%H:%M")}',
            'date': today,
            'clock_in': attendance.time_in,
            'clock_out': None,
            'hours_worked': None,
        })

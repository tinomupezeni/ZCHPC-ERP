from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

from ..models import Notification
from ..serializers.dashboard_serializers import (
    NotificationSerializer,
    DashboardSummarySerializer,
)
from human_resources.hr_models import (
    LeaveRequest,
    LeaveBalance,
    LeaveType,
    AttendanceRecord,
    CompanyEvent,
)


class DashboardView(APIView):
    """
    Get dashboard summary data for the logged-in employee.

    GET /api/portal/dashboard/
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
        start_of_month = today.replace(day=1)

        # Get leave balances
        leave_balances = []
        total_leave_balance = 0

        try:
            balances = LeaveBalance.objects.filter(
                employee=employee
            ).select_related('leave_type')

            for balance in balances:
                # Calculate pending days from pending leave requests
                pending_requests = LeaveRequest.objects.filter(
                    employee=employee,
                    leave_type=balance.leave_type,
                    status='Pending'
                )
                pending_days = sum(
                    (r.end_date - r.start_date).days + 1 for r in pending_requests
                )

                available = balance.balance - pending_days
                total_leave_balance += available

                leave_balances.append({
                    'leave_type': balance.leave_type.name,
                    'leave_type_id': balance.leave_type.id,
                    'total_days': balance.leave_type.default_days_allowed,
                    'used_days': balance.leave_type.default_days_allowed - balance.balance,
                    'pending_days': pending_days,
                    'available_days': max(0, available),
                })
        except Exception:
            # LeaveBalance might not exist for this employee
            total_leave_balance = employee.leave_days_entitled or 0
            leave_balances = [{
                'leave_type': 'Annual Leave',
                'leave_type_id': 0,
                'total_days': total_leave_balance,
                'used_days': 0,
                'pending_days': 0,
                'available_days': total_leave_balance,
            }]

        # Get pending requests count
        pending_leave_requests = LeaveRequest.objects.filter(
            employee=employee,
            status='Pending'
        ).count()

        # Pending expense claims (will be 0 until expense module is implemented)
        pending_expense_claims = 0

        # Open tickets (will be 0 until ticket module is implemented)
        open_tickets = 0

        # Attendance this month
        attendance_this_month = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=start_of_month,
            date__lte=today
        ).count()

        # Today's clock status
        today_status = 'not_clocked'
        try:
            today_attendance = AttendanceRecord.objects.filter(
                employee=employee,
                date=today
            ).first()
            if today_attendance:
                if today_attendance.time_out:
                    today_status = 'clocked_out'
                elif today_attendance.time_in:
                    today_status = 'clocked_in'
        except Exception:
            pass

        # Recent attendance (last 7 days)
        recent_attendance = []
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=today - timedelta(days=7),
            date__lte=today
        ).order_by('-date')[:7]

        for record in attendance_records:
            recent_attendance.append({
                'date': record.date,
                'clock_in': record.time_in,
                'clock_out': record.time_out,
                'status': 'present' if record.time_in else 'absent',
            })

        # Upcoming events (next 30 days)
        upcoming_events = CompanyEvent.objects.filter(
            start_date__gte=today,
            start_date__lte=today + timedelta(days=30)
        ).order_by('start_date')[:5]

        # Unread notifications count
        unread_notifications = Notification.objects.filter(
            employee=employee,
            is_read=False
        ).count()

        # Build response
        data = {
            'employee_name': f"{employee.first_name} {employee.surname}",
            'employee_id': employee.employee_id,
            'position': employee.position.title if employee.position else None,
            'department': employee.department.name if employee.department else None,
            'total_leave_balance': total_leave_balance,
            'leave_balances': leave_balances,
            'pending_leave_requests': pending_leave_requests,
            'pending_expense_claims': pending_expense_claims,
            'open_tickets': open_tickets,
            'attendance_this_month': attendance_this_month,
            'today_status': today_status,
            'recent_attendance': recent_attendance,
            'upcoming_events': upcoming_events,
            'unread_notifications': unread_notifications,
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for employee notifications.

    GET /api/portal/notifications/ - List notifications
    GET /api/portal/notifications/{id}/ - Get notification detail
    PATCH /api/portal/notifications/{id}/read/ - Mark as read
    POST /api/portal/notifications/mark-all-read/ - Mark all as read
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Notification.objects.none()

        queryset = Notification.objects.filter(employee=employee)

        # Filter by read status if provided
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        # Filter by type if provided
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        now = timezone.now()
        updated = Notification.objects.filter(
            employee=employee,
            is_read=False
        ).update(is_read=True, read_at=now)

        return Response({
            'detail': f'Marked {updated} notifications as read'
        })

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        user = request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            return Response({'count': 0})

        count = Notification.objects.filter(
            employee=employee,
            is_read=False
        ).count()

        return Response({'count': count})

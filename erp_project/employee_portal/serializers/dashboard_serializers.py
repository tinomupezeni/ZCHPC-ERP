from rest_framework import serializers
from ..models import Notification
from human_resources.hr_models import CompanyEvent


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for employee notifications."""

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'read_at',
            'related_object_type',
            'related_object_id',
        ]
        read_only_fields = ['id', 'created_at']


class LeaveBalanceSerializer(serializers.Serializer):
    """Serializer for leave balance summary."""
    leave_type = serializers.CharField()
    leave_type_id = serializers.IntegerField()
    total_days = serializers.IntegerField()
    used_days = serializers.IntegerField()
    pending_days = serializers.IntegerField()
    available_days = serializers.IntegerField()


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary."""
    date = serializers.DateField()
    clock_in = serializers.TimeField(allow_null=True)
    clock_out = serializers.TimeField(allow_null=True)
    status = serializers.CharField()  # present, absent, late, leave


class UpcomingEventSerializer(serializers.ModelSerializer):
    """Serializer for upcoming company events."""

    class Meta:
        model = CompanyEvent
        fields = [
            'id',
            'title',
            'event_type',
            'start_date',
            'end_date',
            'description',
            'is_all_day',
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for the complete dashboard summary."""
    employee_name = serializers.CharField()
    employee_id = serializers.CharField()
    position = serializers.CharField(allow_null=True)
    department = serializers.CharField(allow_null=True)

    # Leave summary
    total_leave_balance = serializers.IntegerField()
    leave_balances = LeaveBalanceSerializer(many=True)

    # Requests summary
    pending_leave_requests = serializers.IntegerField()
    pending_expense_claims = serializers.IntegerField()
    open_tickets = serializers.IntegerField()

    # Attendance
    attendance_this_month = serializers.IntegerField()
    today_status = serializers.CharField()  # clocked_in, clocked_out, not_clocked

    # Recent items
    recent_attendance = AttendanceSummarySerializer(many=True)
    upcoming_events = UpcomingEventSerializer(many=True)

    # Notifications
    unread_notifications = serializers.IntegerField()

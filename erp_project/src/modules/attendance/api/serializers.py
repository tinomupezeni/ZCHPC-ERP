"""
Attendance API serializers.
"""

from rest_framework import serializers


# =============================================================================
# Request Serializers
# =============================================================================


class ClockInRequestSerializer(serializers.Serializer):
    """Serializer for clock-in requests."""

    # Clock time is optional - defaults to current time
    clock_time = serializers.DateTimeField(required=False, allow_null=True)


class ClockOutRequestSerializer(serializers.Serializer):
    """Serializer for clock-out requests."""

    clock_time = serializers.DateTimeField(required=False, allow_null=True)


class QRClockInRequestSerializer(serializers.Serializer):
    """Serializer for QR clock-in requests."""

    token = serializers.CharField(max_length=64, required=True)


class UpdateAttendanceRequestSerializer(serializers.Serializer):
    """Serializer for updating attendance records."""

    time_in = serializers.TimeField(required=False, allow_null=True)
    time_out = serializers.TimeField(required=False, allow_null=True)


class AttendanceHistoryQuerySerializer(serializers.Serializer):
    """Serializer for attendance history query parameters."""

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)


class AttendanceSummaryQuerySerializer(serializers.Serializer):
    """Serializer for attendance summary query parameters."""

    year = serializers.IntegerField(required=False)
    month = serializers.IntegerField(required=False, min_value=1, max_value=12)


class AdminAttendanceQuerySerializer(serializers.Serializer):
    """Serializer for admin attendance list query parameters."""

    department_id = serializers.IntegerField(required=False)
    employee_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=200)


# =============================================================================
# Response Serializers
# =============================================================================


class AttendanceRecordResponseSerializer(serializers.Serializer):
    """Serializer for attendance record responses."""

    id = serializers.IntegerField()
    employee_id = serializers.IntegerField()
    record_date = serializers.DateField()
    time_in = serializers.TimeField(allow_null=True)
    time_out = serializers.TimeField(allow_null=True)
    status = serializers.CharField()
    hours_worked = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_late = serializers.BooleanField()


class ClockResponseSerializer(serializers.Serializer):
    """Serializer for clock in/out responses."""

    action = serializers.CharField()
    message = serializers.CharField()
    record = AttendanceRecordResponseSerializer()


class AttendanceSummaryResponseSerializer(serializers.Serializer):
    """Serializer for attendance summary responses."""

    employee_id = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    days_present = serializers.IntegerField()
    days_absent = serializers.IntegerField()
    days_late = serializers.IntegerField()
    days_half_day = serializers.IntegerField()
    days_on_leave = serializers.IntegerField()
    total_hours_worked = serializers.DecimalField(max_digits=7, decimal_places=2)
    average_hours_per_day = serializers.DecimalField(max_digits=5, decimal_places=2)
    attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class AttendanceHistoryResponseSerializer(serializers.Serializer):
    """Serializer for paginated attendance history responses."""

    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results = AttendanceRecordResponseSerializer(many=True)


class AdminAttendanceRecordResponseSerializer(AttendanceRecordResponseSerializer):
    """Attendance record enriched with employee/department names for admin views."""

    employee_name = serializers.CharField()
    department_name = serializers.CharField(allow_null=True)


class AdminAttendanceListResponseSerializer(serializers.Serializer):
    """Serializer for paginated admin attendance list responses."""

    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    results = AdminAttendanceRecordResponseSerializer(many=True)


class QRTokenResponseSerializer(serializers.Serializer):
    """Serializer for QR token responses."""

    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    seconds_remaining = serializers.IntegerField()


class QRClockInResponseSerializer(serializers.Serializer):
    """Serializer for QR clock-in responses."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    action = serializers.CharField(required=False)
    record = AttendanceRecordResponseSerializer(required=False)

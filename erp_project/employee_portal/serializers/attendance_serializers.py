from rest_framework import serializers
from human_resources.hr_models import AttendanceRecord
from django.utils import timezone


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for attendance records."""
    employee_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = [
            'id',
            'employee',
            'employee_name',
            'date',
            'time_in',
            'time_out',
            'status',
        ]
        read_only_fields = ['id', 'employee', 'employee_name']

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.surname}"

    def get_status(self, obj):
        if obj.time_in and obj.time_out:
            return 'complete'
        elif obj.time_in:
            return 'clocked_in'
        return 'absent'


class ClockInOutSerializer(serializers.Serializer):
    """Serializer for clock in/out requests."""
    qr_token = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_qr_token(self, value):
        # QR token validation will be implemented when QR system is set up
        # For now, allow manual clock in/out
        return value


class AttendanceStatusSerializer(serializers.Serializer):
    """Serializer for today's attendance status."""
    date = serializers.DateField()
    clock_in = serializers.TimeField(allow_null=True)
    clock_out = serializers.TimeField(allow_null=True)
    status = serializers.CharField()  # not_clocked, clocked_in, clocked_out
    hours_worked = serializers.DecimalField(max_digits=4, decimal_places=2, allow_null=True)


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for monthly attendance summary."""
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_working_days = serializers.IntegerField()
    days_present = serializers.IntegerField()
    days_absent = serializers.IntegerField()
    days_late = serializers.IntegerField()
    days_on_leave = serializers.IntegerField()
    total_hours_worked = serializers.DecimalField(max_digits=6, decimal_places=2)
    average_clock_in = serializers.TimeField(allow_null=True)
    average_clock_out = serializers.TimeField(allow_null=True)


class AttendanceHistorySerializer(serializers.Serializer):
    """Serializer for attendance history list."""
    records = AttendanceRecordSerializer(many=True)
    total_count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()

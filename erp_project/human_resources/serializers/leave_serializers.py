from rest_framework import serializers
from ..hr_models import LeaveRequest, LeaveType, LeaveBalance, CompanyEvent


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'default_days_allowed']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ['id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
                  'year', 'days_allowed', 'days_used', 'days_remaining']

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.surname}"


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    number_of_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'number_of_days', 'reason', 'status',
            'requested_on', 'reviewed_by', 'reviewed_by_name', 'review_date'
        ]
        read_only_fields = ['requested_on', 'review_date']

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.surname}"

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.surname}"
        return None


class CompanyEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CompanyEvent
        fields = [
            'id', 'title', 'description', 'event_type', 'start_date', 'end_date',
            'start_time', 'end_time', 'is_all_day', 'location',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.surname}"
        return None

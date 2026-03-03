from rest_framework import serializers
from human_resources.hr_models import LeaveType, LeaveBalance, LeaveRequest
from django.utils import timezone
from datetime import timedelta


class PortalLeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for leave types (read-only for employees)"""
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'default_days_allowed']


class PortalLeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for employee's leave balance"""
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    days_allowed = serializers.DecimalField(
        source='leave_type.default_days_allowed',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    days_used = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'leave_type', 'leave_type_name', 'year',
            'days_allowed', 'days_remaining', 'days_used', 'percentage_used'
        ]

    def get_days_used(self, obj):
        days_allowed = obj.leave_type.default_days_allowed
        return float(days_allowed) - float(obj.days_remaining)

    def get_percentage_used(self, obj):
        days_allowed = obj.leave_type.default_days_allowed
        if days_allowed > 0:
            days_used = float(days_allowed) - float(obj.days_remaining)
            return round((days_used / days_allowed) * 100, 1)
        return 0


class PortalLeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for employee's leave requests"""
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    number_of_days = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'leave_type', 'leave_type_name', 'start_date', 'end_date',
            'number_of_days', 'reason', 'status', 'requested_on',
            'reviewed_by_name', 'review_date', 'can_cancel'
        ]
        read_only_fields = ['status', 'requested_on', 'review_date']

    def get_number_of_days(self, obj):
        """Calculate number of days from start_date and end_date"""
        return (obj.end_date - obj.start_date).days + 1

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return f"{obj.reviewed_by.first_name} {obj.reviewed_by.surname}"
        return None

    def get_can_cancel(self, obj):
        """Check if the request can be cancelled"""
        return obj.status == 'Pending'


class CreateLeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating a new leave request"""
    number_of_days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = ['id', 'leave_type', 'start_date', 'end_date', 'reason', 'number_of_days']

    def get_number_of_days(self, obj):
        """Calculate number of days from start_date and end_date"""
        return (obj.end_date - obj.start_date).days + 1

    def validate(self, data):
        """Validate the leave request"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type = data.get('leave_type')
        employee = self.context['request'].user.employee_profile

        # Validate dates
        if start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after or equal to start date.'
            })

        # Cannot request leave in the past
        if start_date < timezone.now().date():
            raise serializers.ValidationError({
                'start_date': 'Cannot request leave for past dates.'
            })

        # Calculate number of days
        num_days = (end_date - start_date).days + 1

        # Check leave balance
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_type=leave_type,
                year=current_year
            )
            if num_days > float(balance.days_remaining):
                raise serializers.ValidationError({
                    'leave_type': f'Insufficient leave balance. You have {balance.days_remaining} days remaining.'
                })
        except LeaveBalance.DoesNotExist:
            raise serializers.ValidationError({
                'leave_type': 'No leave balance found for this leave type.'
            })

        # Check for overlapping requests
        overlapping = LeaveRequest.objects.filter(
            employee=employee,
            status__in=['Pending', 'Approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()

        if overlapping:
            raise serializers.ValidationError({
                'start_date': 'You already have a leave request for these dates.'
            })

        return data

    def create(self, validated_data):
        """Create a new leave request for the current employee"""
        employee = self.context['request'].user.employee_profile
        validated_data['employee'] = employee
        return super().create(validated_data)


class LeaveRequestSummarySerializer(serializers.Serializer):
    """Serializer for leave request summary stats"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    rejected_requests = serializers.IntegerField()
    total_days_taken = serializers.DecimalField(max_digits=5, decimal_places=1)

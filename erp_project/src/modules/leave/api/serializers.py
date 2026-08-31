"""
Leave API serializers.
"""

from rest_framework import serializers


# =============================================================================
# Request Serializers
# =============================================================================


class CreateLeaveTypeRequestSerializer(serializers.Serializer):
    """Serializer for creating a leave type."""

    name = serializers.CharField(max_length=100)
    default_days_allowed = serializers.IntegerField(default=0, min_value=0)
    is_active = serializers.BooleanField(default=True)


class UpdateLeaveTypeRequestSerializer(serializers.Serializer):
    """Serializer for updating a leave type."""

    name = serializers.CharField(max_length=100, required=False)
    default_days_allowed = serializers.IntegerField(min_value=0, required=False)
    is_active = serializers.BooleanField(required=False)


class SetLeaveEntitlementRequestSerializer(serializers.Serializer):
    """Serializer for setting leave entitlement."""

    employee_id = serializers.IntegerField()
    leave_type_id = serializers.IntegerField()
    year = serializers.IntegerField()
    entitled_days = serializers.DecimalField(max_digits=5, decimal_places=2)


class AdjustLeaveBalanceRequestSerializer(serializers.Serializer):
    """Serializer for adjusting leave balance."""

    adjustment_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    reason = serializers.CharField(max_length=500)


class SubmitLeaveRequestSerializer(serializers.Serializer):
    """Serializer for submitting a leave request."""

    leave_type_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate(self, data):
        """Validate date range."""
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return data


class ReviewLeaveRequestSerializer(serializers.Serializer):
    """Serializer for reviewing (approve/reject) a leave request."""

    approved = serializers.BooleanField()
    rejection_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class LeaveRequestQuerySerializer(serializers.Serializer):
    """Serializer for leave request query parameters."""

    year = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        choices=["Pending", "Approved", "Rejected", "Cancelled"],
        required=False,
    )


class LeaveBalanceQuerySerializer(serializers.Serializer):
    """Serializer for leave balance query parameters."""

    year = serializers.IntegerField(required=False)


# =============================================================================
# Response Serializers
# =============================================================================


class LeaveTypeResponseSerializer(serializers.Serializer):
    """Serializer for leave type responses."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    default_days_allowed = serializers.IntegerField()
    is_active = serializers.BooleanField()


class LeaveBalanceResponseSerializer(serializers.Serializer):
    """Serializer for leave balance responses."""

    id = serializers.IntegerField()
    employee_id = serializers.IntegerField()
    leave_type_id = serializers.IntegerField()
    leave_type_name = serializers.CharField()
    year = serializers.IntegerField()
    entitled_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    used_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    remaining_days = serializers.DecimalField(max_digits=5, decimal_places=2)
    usage_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class LeaveBalanceSummaryResponseSerializer(serializers.Serializer):
    """Serializer for leave balance summary responses."""

    employee_id = serializers.IntegerField()
    year = serializers.IntegerField()
    total_entitled = serializers.DecimalField(max_digits=7, decimal_places=2)
    total_used = serializers.DecimalField(max_digits=7, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=7, decimal_places=2)
    balances = LeaveBalanceResponseSerializer(many=True)


class LeaveRequestResponseSerializer(serializers.Serializer):
    """Serializer for leave request responses."""

    id = serializers.IntegerField()
    employee_id = serializers.IntegerField()
    leave_type_id = serializers.IntegerField()
    leave_type_name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = serializers.IntegerField()
    reason = serializers.CharField()
    status = serializers.CharField()
    can_cancel = serializers.BooleanField()
    requested_at = serializers.CharField()
    reviewed_by_id = serializers.IntegerField(allow_null=True)
    reviewed_at = serializers.CharField(allow_null=True)


class AdminLeaveRequestResponseSerializer(serializers.Serializer):
    """
    Leave request serializer for the admin-wide listing (all employees, all
    statuses). Field names match the HR admin frontend's LeaveRequest
    interface exactly - unlike LeaveRequestResponseSerializer, which is
    shaped for the employee self-service DTO instead.
    """

    id = serializers.IntegerField()
    employee = serializers.IntegerField(source="employee_id")
    employee_name = serializers.SerializerMethodField()
    leave_type = serializers.IntegerField(source="leave_type_id")
    leave_type_name = serializers.CharField(source="leave_type.name")
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    number_of_days = serializers.IntegerField()
    reason = serializers.CharField()
    status = serializers.CharField()
    requested_on = serializers.DateTimeField()
    reviewed_by = serializers.IntegerField(source="reviewed_by_id", allow_null=True)
    reviewed_by_name = serializers.SerializerMethodField()
    review_date = serializers.DateTimeField(allow_null=True)

    def get_employee_name(self, obj) -> str:
        return f"{obj.employee.first_name} {obj.employee.surname}".strip()

    def get_reviewed_by_name(self, obj) -> str | None:
        if not obj.reviewed_by_id:
            return None
        return f"{obj.reviewed_by.first_name} {obj.reviewed_by.surname}".strip()


class LeaveRequestSummaryResponseSerializer(serializers.Serializer):
    """Serializer for leave request summary responses."""

    employee_id = serializers.IntegerField()
    year = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    rejected_requests = serializers.IntegerField()
    cancelled_requests = serializers.IntegerField()
    total_days_taken = serializers.IntegerField()

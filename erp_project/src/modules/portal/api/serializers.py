"""
API serializers for the portal module.
"""

from rest_framework import serializers


# ============================
# Authentication Serializers
# ============================

class LoginSerializer(serializers.Serializer):
    """Serializer for portal login."""

    ec_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)


class EmployeeProfileSerializer(serializers.Serializer):
    """Serializer for employee profile."""

    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.CharField()
    first_name = serializers.CharField()
    surname = serializers.CharField()
    email = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    department_id = serializers.IntegerField(allow_null=True)
    department_name = serializers.CharField(allow_null=True)
    position_id = serializers.IntegerField(allow_null=True)
    position_name = serializers.CharField(allow_null=True)


# ============================
# Dashboard Serializers
# ============================

class LeaveBalanceSerializer(serializers.Serializer):
    """Serializer for leave balance."""

    leave_type_id = serializers.IntegerField()
    leave_type_name = serializers.CharField()
    entitled_days = serializers.IntegerField()
    used_days = serializers.IntegerField()
    pending_days = serializers.IntegerField()
    remaining_days = serializers.IntegerField()


class AttendanceRecordSerializer(serializers.Serializer):
    """Serializer for attendance record."""

    id = serializers.IntegerField()
    date = serializers.DateField()
    time_in = serializers.DateTimeField(allow_null=True)
    time_out = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()


class CompanyEventSerializer(serializers.Serializer):
    """Serializer for company event."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    event_date = serializers.DateField()
    event_type = serializers.CharField()


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data."""

    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    department_name = serializers.CharField(allow_null=True)
    position_name = serializers.CharField(allow_null=True)
    leave_balances = LeaveBalanceSerializer(many=True)
    today_clock_status = AttendanceRecordSerializer(allow_null=True)
    monthly_attendance_count = serializers.IntegerField()
    recent_attendance = AttendanceRecordSerializer(many=True)
    pending_leave_requests = serializers.IntegerField()
    pending_expense_claims = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    upcoming_events = CompanyEventSerializer(many=True)


# ============================
# Attendance Serializers
# ============================

class ClockStatusSerializer(serializers.Serializer):
    """Serializer for clock status."""

    is_clocked_in = serializers.BooleanField()
    clock_in_time = serializers.DateTimeField(allow_null=True)
    clock_out_time = serializers.DateTimeField(allow_null=True)
    worked_hours = serializers.FloatField(allow_null=True)


class QRClockSerializer(serializers.Serializer):
    """Serializer for QR clock in/out."""

    token = serializers.CharField()


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary."""

    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    leave_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    total_hours = serializers.FloatField()


# ============================
# Leave Serializers
# ============================

class LeaveRequestSerializer(serializers.Serializer):
    """Serializer for leave request."""

    id = serializers.IntegerField(read_only=True)
    leave_type_id = serializers.IntegerField()
    leave_type_name = serializers.CharField(read_only=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days_count = serializers.IntegerField(read_only=True)
    reason = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class CreateLeaveRequestSerializer(serializers.Serializer):
    """Serializer for creating leave request."""

    leave_type_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_null=True)


# ============================
# Payslip Serializers
# ============================

class PayslipSerializer(serializers.Serializer):
    """Serializer for payslip."""

    id = serializers.IntegerField()
    period_year = serializers.IntegerField()
    period_month = serializers.IntegerField()
    gross_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    gross_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deductions_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deductions_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.CharField()


# ============================
# Public Careers Serializers
# ============================

class JobListingSerializer(serializers.Serializer):
    """Serializer for job listing."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    department_name = serializers.CharField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    salary_usd_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    salary_usd_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    posted_date = serializers.DateField(allow_null=True)


class JobDetailSerializer(serializers.Serializer):
    """Serializer for job detail."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    department_name = serializers.CharField(allow_null=True)
    location = serializers.CharField(allow_null=True)
    salary_usd_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    salary_usd_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    description = serializers.CharField()
    qualifications = serializers.CharField()
    posted_date = serializers.DateField(allow_null=True)


class JobApplicationSerializer(serializers.Serializer):
    """Serializer for job application."""

    national_id = serializers.CharField(max_length=50)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    qualifications = serializers.CharField(required=False, allow_null=True)
    experience = serializers.CharField(required=False, allow_null=True)
    cover_letter = serializers.CharField(required=False, allow_null=True)


class ApplicationStatusSerializer(serializers.Serializer):
    """Serializer for application status."""

    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    applied_at = serializers.CharField()
    status = serializers.CharField()


# ============================
# Notification Serializers
# ============================

class NotificationSerializer(serializers.Serializer):
    """Serializer for notification."""

    id = serializers.IntegerField()
    notification_type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    is_read = serializers.BooleanField()
    read_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()

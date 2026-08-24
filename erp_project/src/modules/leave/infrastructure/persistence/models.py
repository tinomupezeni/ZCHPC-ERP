"""
Django models for the Leave module.
"""
from django.db import models
from django.utils import timezone


class LeaveType(models.Model):
    """Type of leave (Annual, Sick, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    default_days_allowed = models.IntegerField(default=0)

    class Meta:
        db_table = 'human_resources_leavetype'

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    """Tracks remaining leave days for each employee."""
    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField(default=timezone.now().year)
    days_remaining = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'human_resources_leavebalance'
        unique_together = ('employee', 'leave_type', 'year')

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.year})"


class LeaveRequest(models.Model):
    """Employee leave request."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'), ('Approved', 'Approved'),
        ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')
    ]

    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_on = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        'hr.Employees',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_leave_requests'
    )
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'human_resources_leaverequest'
        ordering = ['-requested_on']

    @property
    def number_of_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name}"


class CompanyEvent(models.Model):
    """Company calendar events."""
    EVENT_TYPE_CHOICES = [
        ('Holiday', 'Public Holiday'), ('Company', 'Company Event'),
        ('Meeting', 'Meeting'), ('Training', 'Training'), ('Other', 'Other')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='Company')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        'hr.Employees',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'human_resources_companyevent'
        ordering = ['start_date', 'start_time']

    def __str__(self):
        return f"{self.title} ({self.start_date})"

# Phase 1: New Normalized Models for Leave
class LeaveProfile(models.Model):
    employee = models.OneToOneField('hr.Employees', on_delete=models.CASCADE, related_name='leave_profile')
    leave_days_entitled = models.IntegerField(default=20)
    accrual_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.67) # e.g. 20/12 months

    class Meta:
        db_table = 'leave_leaveprofile'

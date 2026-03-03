from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from ..hr_models import LeaveRequest, LeaveType, LeaveBalance, CompanyEvent
from ..serializers.leave_serializers import (
    LeaveRequestSerializer,
    LeaveTypeSerializer,
    LeaveBalanceSerializer,
    CompanyEventSerializer
)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """CRUD operations for Leave Types"""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    """View and manage leave balances"""
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = LeaveBalance.objects.all()
        employee_id = self.request.query_params.get('employee', None)
        year = self.request.query_params.get('year', None)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if year:
            queryset = queryset.filter(year=year)

        return queryset


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """CRUD operations for Leave Requests with approval workflow"""
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related(
            'employee', 'leave_type', 'reviewed_by'
        ).all()

        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave request"""
        leave_request = self.get_object()

        if leave_request.status != 'Pending':
            return Response(
                {'error': 'Only pending requests can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the reviewer (current user's employee profile)
        reviewer = getattr(request.user, 'employee_profile', None)

        leave_request.status = 'Approved'
        leave_request.reviewed_by = reviewer
        leave_request.review_date = timezone.now()
        leave_request.save()

        # Update leave balance
        try:
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=leave_request.start_date.year
            )
            balance.days_used += leave_request.number_of_days
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass  # Balance record doesn't exist

        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a leave request"""
        leave_request = self.get_object()

        if leave_request.status != 'Pending':
            return Response(
                {'error': 'Only pending requests can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reviewer = getattr(request.user, 'employee_profile', None)

        leave_request.status = 'Rejected'
        leave_request.reviewed_by = reviewer
        leave_request.review_date = timezone.now()
        leave_request.save()

        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)


class CompanyEventViewSet(viewsets.ModelViewSet):
    """CRUD operations for Company Calendar Events"""
    queryset = CompanyEvent.objects.all()
    serializer_class = CompanyEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CompanyEvent.objects.select_related('created_by').all()

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        event_type = self.request.query_params.get('event_type', None)

        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset

    def perform_create(self, serializer):
        # Set the created_by to current user's employee profile
        employee = getattr(self.request.user, 'employee_profile', None)
        serializer.save(created_by=employee)

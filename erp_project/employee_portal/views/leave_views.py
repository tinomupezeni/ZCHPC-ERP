from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Sum, Q
from human_resources.hr_models import LeaveType, LeaveBalance, LeaveRequest
from ..serializers.leave_serializers import (
    PortalLeaveTypeSerializer,
    PortalLeaveBalanceSerializer,
    PortalLeaveRequestSerializer,
    CreateLeaveRequestSerializer,
    LeaveRequestSummarySerializer,
)


class LeaveTypeListView(APIView):
    """List all available leave types"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leave_types = LeaveType.objects.all()
        serializer = PortalLeaveTypeSerializer(leave_types, many=True)
        return Response(serializer.data)


class LeaveBalanceView(APIView):
    """Get employee's leave balances"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )
        year = request.query_params.get('year', timezone.now().year)

        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=year
        ).select_related('leave_type')

        serializer = PortalLeaveBalanceSerializer(balances, many=True)

        # Calculate totals
        total_allowed = sum(b.leave_type.default_days_allowed for b in balances)
        total_remaining = sum(float(b.days_remaining) for b in balances)
        total_used = total_allowed - total_remaining

        return Response({
            'year': year,
            'balances': serializer.data,
            'summary': {
                'total_allowed': total_allowed,
                'total_used': round(total_used, 1),
                'total_remaining': round(total_remaining, 1),
            }
        })


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing employee's leave requests"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateLeaveRequestSerializer
        return PortalLeaveRequestSerializer

    def get_queryset(self):
        """Filter to only the employee's own requests"""
        employee = getattr(self.request.user, 'employee_profile', None)
        if not employee:
            return LeaveRequest.objects.none()
        queryset = LeaveRequest.objects.filter(
            employee=employee
        ).select_related('leave_type', 'reviewed_by')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(start_date__year=year)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create a new leave request"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave_request = serializer.save()

        # Return the full response with computed fields
        response_serializer = PortalLeaveRequestSerializer(leave_request)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Cancel a pending leave request"""
        instance = self.get_object()

        if instance.status != 'Pending':
            return Response(
                {'detail': 'Only pending requests can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.status = 'Cancelled'
        instance.save()

        return Response(
            {'detail': 'Leave request cancelled successfully.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for the employee's leave requests"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )
        year = request.query_params.get('year', timezone.now().year)

        requests = LeaveRequest.objects.filter(
            employee=employee,
            start_date__year=year
        )

        # Calculate stats
        total_requests = requests.count()
        pending_requests = requests.filter(status='Pending').count()
        approved_requests = requests.filter(status='Approved').count()
        rejected_requests = requests.filter(status='Rejected').count()

        # Calculate total days taken (approved requests only)
        approved = requests.filter(status='Approved')
        total_days_taken = sum((r.end_date - r.start_date).days + 1 for r in approved)

        data = {
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
            'total_days_taken': total_days_taken,
        }

        serializer = LeaveRequestSummarySerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get leave requests in calendar format"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response([])
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month')

        queryset = LeaveRequest.objects.filter(
            employee=employee,
            status__in=['Pending', 'Approved'],
            start_date__year=year
        ).select_related('leave_type')

        if month:
            queryset = queryset.filter(
                Q(start_date__month=month) | Q(end_date__month=month)
            )

        # Format for calendar display
        events = []
        for leave in queryset:
            events.append({
                'id': leave.id,
                'title': leave.leave_type.name,
                'start': leave.start_date.isoformat(),
                'end': leave.end_date.isoformat(),
                'status': leave.status,
                'days': (leave.end_date - leave.start_date).days + 1,
            })

        return Response(events)


class LeaveRequestCancelView(APIView):
    """Cancel a pending leave request"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            leave_request = LeaveRequest.objects.get(
                pk=pk,
                employee=employee
            )
        except LeaveRequest.DoesNotExist:
            return Response(
                {'detail': 'Leave request not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if leave_request.status != 'Pending':
            return Response(
                {'detail': 'Only pending requests can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        leave_request.status = 'Cancelled'
        leave_request.save()

        return Response({
            'detail': 'Leave request cancelled successfully.',
            'request': PortalLeaveRequestSerializer(leave_request).data
        })

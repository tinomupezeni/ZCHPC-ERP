from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db.models import Sum, Q
from ..models import ExpenseCategory, ExpenseClaim
from ..serializers.expense_serializers import (
    ExpenseCategorySerializer,
    ExpenseClaimListSerializer,
    ExpenseClaimDetailSerializer,
    CreateExpenseClaimSerializer,
    UpdateExpenseClaimSerializer,
    ExpenseClaimSummarySerializer,
)


class ExpenseCategoryListView(APIView):
    """List all active expense categories"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = ExpenseCategory.objects.filter(is_active=True)
        serializer = ExpenseCategorySerializer(categories, many=True)
        return Response(serializer.data)


class ExpenseClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expense claims"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateExpenseClaimSerializer
        if self.action in ['update', 'partial_update']:
            return UpdateExpenseClaimSerializer
        if self.action == 'retrieve':
            return ExpenseClaimDetailSerializer
        return ExpenseClaimListSerializer

    def get_queryset(self):
        """Filter to only the employee's own claims"""
        employee = getattr(self.request.user, 'employee_profile', None)
        if not employee:
            return ExpenseClaim.objects.none()
        queryset = ExpenseClaim.objects.filter(
            employee=employee
        ).select_related('category', 'reviewed_by')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date_incurred__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_incurred__lte=end_date)

        return queryset

    def destroy(self, request, *args, **kwargs):
        """Delete only draft claims"""
        instance = self.get_object()

        if instance.status != 'Draft':
            return Response(
                {'detail': 'Only draft claims can be deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete associated receipt file
        if instance.receipt:
            instance.receipt.delete(save=False)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft claim for review"""
        claim = self.get_object()

        if claim.status != 'Draft':
            return Response(
                {'detail': 'Only draft claims can be submitted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if receipt is required
        if claim.category.requires_receipt and not claim.receipt:
            return Response(
                {'detail': 'A receipt is required for this category.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'Submitted'
        claim.submitted_at = timezone.now()
        claim.save()

        serializer = ExpenseClaimDetailSerializer(claim, context={'request': request})
        return Response({
            'detail': 'Expense claim submitted successfully.',
            'claim': serializer.data
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a draft or submitted claim"""
        claim = self.get_object()

        if claim.status not in ['Draft', 'Submitted']:
            return Response(
                {'detail': 'Only draft or submitted claims can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete the claim instead of changing status
        if claim.receipt:
            claim.receipt.delete(save=False)
        claim.delete()

        return Response({'detail': 'Expense claim cancelled successfully.'})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of employee's expense claims"""
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        claims = ExpenseClaim.objects.filter(employee=employee)

        # Count by status
        total_claims = claims.count()
        draft_claims = claims.filter(status='Draft').count()
        pending_claims = claims.filter(status__in=['Submitted', 'Under Review']).count()
        approved_claims = claims.filter(status='Approved').count()
        rejected_claims = claims.filter(status='Rejected').count()
        paid_claims = claims.filter(status='Paid').count()

        # Sum amounts by status (USD only for simplicity)
        total_amount_pending = claims.filter(
            status__in=['Submitted', 'Under Review'],
            currency='USD'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_amount_approved = claims.filter(
            status='Approved',
            currency='USD'
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_amount_paid = claims.filter(
            status='Paid',
            currency='USD'
        ).aggregate(total=Sum('amount'))['total'] or 0

        data = {
            'total_claims': total_claims,
            'draft_claims': draft_claims,
            'pending_claims': pending_claims,
            'approved_claims': approved_claims,
            'rejected_claims': rejected_claims,
            'paid_claims': paid_claims,
            'total_amount_pending': total_amount_pending,
            'total_amount_approved': total_amount_approved,
            'total_amount_paid': total_amount_paid,
        }

        serializer = ExpenseClaimSummarySerializer(data)
        return Response(serializer.data)

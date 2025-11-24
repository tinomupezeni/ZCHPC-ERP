from datetime import datetime
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum

# Adjust imports to match your project structure
from .payroll_models import Payroll
from .serializers.payroll_serializers import PayrollSerializer
from .services.payroll_services import PayrollService 

class PayrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Payroll records.
    """
    queryset = Payroll.objects.all().select_related('employee').order_by('employee__surname')
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """
        GET /api/payrolls/?period=YYYY-MM
        Lists payroll records for a specific month.
        """
        period_str = request.query_params.get("period")
        if not period_str:
            return Response(
                {"error": "Period parameter (YYYY-MM) is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate format YYYY-MM
            year, month = period_str.split('-')
            
            # Filter by the specific month
            payrolls = self.get_queryset().filter(
                period__year=year, 
                period__month=month
            )
            
            serializer = self.get_serializer(payrolls, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {"error": "Invalid period format. Use YYYY-MM"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def process(self, request):
        """
        POST /api/payrolls/process/
        Triggers the payroll engine for a specific month.
        Payload: { "month": "2025-11" }
        """
        period = request.data.get("month")
        
        if not period:
            return Response(
                {"error": "Month is required (YYYY-MM)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Call the service to calculate payrolls
            result = PayrollService.process_payroll_for_period(period)
            
            # Check if service returned a specific error dict
            if isinstance(result, dict) and "error" in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": f"Payroll processing complete for {period}",
                "details": result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Internal Error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        POST /api/payrolls/{id}/approve/
        Approves a specific payslip by ID.
        """
        try:
            payroll = self.get_object()
            
            if payroll.status == "Processed":
                return Response(
                    {"message": "Payslip is already processed"}, 
                    status=status.HTTP_200_OK
                )

            # Logic to finalize the slip
            payroll.status = "Processed"
            payroll.save()
            
            return Response(
                {"status": "Processed", "id": payroll.id}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/payrolls/summary/?period=YYYY-MM
        Returns totals for the dashboard cards.
        """
        period_str = request.query_params.get('period')
        if not period_str:
            return Response({"error": "Period required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            year, month = period_str.split('-')
            payrolls = self.get_queryset().filter(period__year=year, period__month=month)
            
            # Calculate totals
            totals = payrolls.aggregate(
                total_usd=Sum('base_salary_usd'),
                total_zig=Sum('base_salary_zig'),
                total_net_usd=Sum('net_salary_usd'),
                total_net_zig=Sum('net_salary_zig')
            )
            
            processed_count = payrolls.filter(status='Processed').count()
            
            return Response({
                "total_gross_usd": totals['total_usd'] or 0,
                "total_gross_zig": totals['total_zig'] or 0,
                "total_net_usd": totals['total_net_usd'] or 0,
                "total_net_zig": totals['total_net_zig'] or 0,
                "total_employees": payrolls.count(),
                "processed_count": processed_count
            })
        except ValueError:
             return Response({"error": "Invalid period"}, status=status.HTTP_400_BAD_REQUEST)
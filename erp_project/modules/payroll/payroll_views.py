# erp/views/payroll_views.py
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from erp.models import Payroll
from .serializers.payroll_serializers import PayrollSerializer
from .repositories.payroll_repository import PayrollRepository
from .services.payroll_services import PayrollService  # fixed import typo

class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer

    def list(self, request):
        period_str = request.query_params.get("period")
        if not period_str:
            return Response({"error": "Period is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert "YYYY-MM" → first day of month
        period_date = datetime.strptime(period_str + "-01", "%Y-%m-%d").date()

        # Process missing payrolls first
        PayrollService.process_payroll_for_period(period_str)

        # Fetch all payrolls for that month
        payrolls = Payroll.objects.filter(
            period__year=period_date.year, period__month=period_date.month
        )
        serializer = PayrollSerializer(payrolls, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=["post"])
    def generate_monthly(self, request):
        period = request.data.get("period")
        if not period:
            return Response({"error": "Period is required"}, status=status.HTTP_400_BAD_REQUEST)

        employees = PayrollRepository.list_employees()
        created = []
        for emp in employees:
            payroll = PayrollService.create_employee_payroll(emp, period)
            created.append(payroll.id)
        return Response({"created": created}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'])
    def delete_slip(self, request):
        employee = request.query_params.get('employee')
        period = request.query_params.get('period')
        if not employee or not period:
            return Response({"error": "Employee and period are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payroll = Payroll.objects.get(employee_id=employee, period=period)
            payroll.delete()
            return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Payroll.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=False, methods=["post"])
    def approve_slip(self, request):
        employee = request.data.get("employee")
        period = request.data.get("period")

        try:
            payroll = Payroll.objects.get(employee_id=employee, period=period)
            payroll.status = "Processed"  # or whatever status you use
            payroll.save()

            return Response(
                {"detail": "Payslip approved", "id": payroll.id},
                status=status.HTTP_200_OK,
            )
        except Payroll.DoesNotExist:
            return Response(
                {"detail": "Payslip not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
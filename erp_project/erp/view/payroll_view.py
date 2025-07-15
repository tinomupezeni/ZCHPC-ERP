from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.utils.dateparse import parse_date

from ..serializers.employee_serializers import EmployeePayslipSerializer

from ..serializers.tax_tables_serializers import EmployeeDeductablesSerializer, NSSACapSerializer, PensionFundSerializer, TaxBracketSerializer, ZiGRateSerializer
from ..models import AllowanceType, DeductionType, EmployeeDeductables, Employees, NSSACap, Payroll, PayrollPeriod, PensionFund, TaxBracket, ZiGRateToUSD
from ..serializers import payroll_serializer
from ..services.payroll_processor import PayrollProcessor
from rest_framework import viewsets


@api_view(['POST'])
def generate_monthly_payroll(request):
    """API endpoint to generate payroll for current month"""
    try:
        print("[generate_monthly_payroll] Raw period:", request.data.get("period"))
        period_str = request.data.get('period')
        period = datetime.strptime(period_str, '%Y-%m').date() if period_str else None
        print("[generate_monthly_payroll] Parsed period:", period)

        count = PayrollProcessor.create_monthly_payroll(period)
        print(f"[generate_monthly_payroll] Created {count} payroll records")

        return Response(
            {"message": f"Successfully created {count} payroll records"},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        print("[generate_monthly_payroll] ERROR:", str(e))
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def get_payroll_records(request):
    """Get payroll records with filtering options"""
    period = request.query_params.get('period')
    status_filter = request.query_params.get('status')
    employee_id = request.query_params.get('employee_id')

    print("[get_payroll_records] Params:", request.query_params)

    queryset = Payroll.objects.all().select_related('employee')

    if period:
        try:
            parsed_period = datetime.strptime(period, '%Y-%m').date().replace(day=1)
            print("[get_payroll_records] Filtering by period:", parsed_period)
            queryset = queryset.filter(period=parsed_period)
        except ValueError:
            print("[get_payroll_records] Invalid period format:", period)
            return Response({"error": "Invalid period format. Use YYYY-MM"}, status=400)

    if status_filter:
        print("[get_payroll_records] Filtering by status:", status_filter)
        queryset = queryset.filter(status=status_filter)

    if employee_id:
        print("[get_payroll_records] Filtering by employee_id:", employee_id)
        queryset = queryset.filter(employee__employeeid=employee_id)

    print(f"[get_payroll_records] Query count: {queryset.count()}")
    serializer = payroll_serializer.PayrollSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def update_payroll_status(request, payroll_id):
    """Update status of a payroll record"""
    print("[update_payroll_status] ID:", payroll_id)
    print("[update_payroll_status] Body:", request.data)

    try:
        payroll = Payroll.objects.get(id=payroll_id)
        new_status = request.data.get('status')
        print("[update_payroll_status] New status:", new_status)

        if new_status not in dict(Payroll.STATUS_CHOICES).keys():
            print("[update_payroll_status] Invalid status:", new_status)
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payroll.status = new_status
        payroll.save()
        print("[update_payroll_status] Updated successfully.")

        return Response(
            {"message": "Payroll status updated successfully"},
            status=status.HTTP_200_OK
        )
    except Payroll.DoesNotExist:
        print("[update_payroll_status] Payroll not found.")
        return Response(
            {"error": "Payroll record not found"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def get_current_rate(request):
    """Get the current ZIG to USD exchange rate"""
    try:
        rate = PayrollProcessor.get_current_rate()
        print("[get_current_rate] Found rate:", rate.rate if rate else "None")
        serializer = payroll_serializer.ZiGRateSerializer(rate)
        return Response(serializer.data)
    except ZiGRateToUSD.DoesNotExist:
        print("[get_current_rate] No rate found.")
        return Response(
            {"error": "No exchange rate available"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def payroll_list(request):
    """Get payroll records for a specific month, generate if not exists"""
    period_str = request.query_params.get('period')
    print("[payroll_list] Received period:", period_str)

    if not period_str:
        print("[payroll_list] Missing period.")
        return Response(
            {"error": "Period parameter (YYYY-MM) is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        period = datetime.strptime(period_str, '%Y-%m').date().replace(day=1)
        print("[payroll_list] Parsed period:", period)

        payroll_exists = Payroll.objects.filter(period=period).exists()
        print("[payroll_list] Existing payroll check:", payroll_exists)

        if not payroll_exists:
            print("[payroll_list] Generating payroll...")
            PayrollProcessor.create_monthly_payroll(period)

        active_employees = Employees.objects.filter(isActive=True)
        print("[payroll_list] Active employees count:", active_employees.count())

        for employee in active_employees:
            exists = Payroll.objects.filter(employee=employee, period=period).exists()
            if not exists:
                print(f"[payroll_list] Creating payroll for {employee.employeeid}")
                PayrollProcessor.create_employee_payroll(employee, period)

        payrolls = Payroll.objects.filter(period=period).select_related('employee')
        print("[payroll_list] Payrolls fetched:", payrolls.count())

        serializer = payroll_serializer.PayrollSerializer(payrolls, many=True)
        print("[payroll_list] Serialization complete")

        return Response({
            "period": period_str,
            "generated": not payroll_exists,
            "count": payrolls.count(),
            "data": serializer.data
        })

    except ValueError as ve:
        print("[payroll_list] ValueError:", str(ve))
        return Response(
            {"error": "Invalid period format. Use YYYY-MM"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print("[payroll_list] ERROR:", str(e))
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

from rest_framework.views import APIView

class DeletePayrollSlipView(APIView):
    def delete(self, request, *args, **kwargs):
        employee_id = request.query_params.get("employee")
        period_str = request.query_params.get("period")
        print("[DeletePayrollSlipView] Params:", request.query_params)

        if not employee_id or not period_str:
            print("[DeletePayrollSlipView] Missing employee or period")
            return Response({"error": "Missing employee or period"}, status=status.HTTP_400_BAD_REQUEST)

        period = parse_date(period_str)
        if not period:
            print("[DeletePayrollSlipView] Invalid date format:", period_str)
            return Response({"error": "Invalid date format for period"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            print("[DeletePayrollSlipView] Deleting payroll for:", employee_id, "Period:", period)
            payroll = Payroll.objects.get(employee__employeeid=employee_id, period=period)
            payroll.delete()
            print("[DeletePayrollSlipView] Deleted successfully")
            return Response({"message": "Payroll slip deleted successfully"}, status=status.HTTP_200_OK)
        except Payroll.DoesNotExist:
            print("[DeletePayrollSlipView] Payroll not found")
            return Response({"error": "Payroll slip not found"}, status=status.HTTP_404_NOT_FOUND)


class ZiGRateToUSDViewSet(viewsets.ModelViewSet):
    queryset = ZiGRateToUSD.objects.all()
    serializer_class = ZiGRateSerializer
    filterset_fields = ['date'] # Allow filtering by date

class NSSACapViewSet(viewsets.ModelViewSet):
    queryset = NSSACap.objects.all()
    serializer_class = NSSACapSerializer
    filterset_fields = ['active_from']

class PensionFundViewSet(viewsets.ModelViewSet):
    queryset = PensionFund.objects.all()
    serializer_class = PensionFundSerializer

class EmployeeDeductablesViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDeductables.objects.all().select_related('employee', 'pension_fund')
    serializer_class = EmployeeDeductablesSerializer
    filterset_fields = ['employee__employeeid', 'active']

class TaxBracketViewSet(viewsets.ModelViewSet):
    queryset = TaxBracket.objects.all()
    serializer_class = TaxBracketSerializer
    filterset_fields = ['currency', 'active_from']


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    queryset = PayrollPeriod.objects.all()
    serializer_class = payroll_serializer.PayrollPeriodSerializer


class AllowanceTypeViewSet(viewsets.ModelViewSet):
    queryset = AllowanceType.objects.all()
    serializer_class = payroll_serializer.AllowanceTypeSerializer
    # You might want to add permission classes here:
    # permission_classes = [IsAuthenticated] # Example

class DeductionTypeViewSet(viewsets.ModelViewSet):
    queryset = DeductionType.objects.all()
    serializer_class = payroll_serializer.DeductionTypeSerializer
    
class AllowanceTypeViewSet(viewsets.ModelViewSet):
    queryset = AllowanceType.objects.all()
    serializer_class = payroll_serializer.AllowanceTypeSerializer

class DeductionTypeViewSet(viewsets.ModelViewSet):
    queryset = DeductionType.objects.all()
    serializer_class = payroll_serializer.DeductionTypeSerializer

class UpdateEmployeeSalaryView(APIView):
    """
    API endpoint to update an employee's salary details,
    including base salaries, allowances, and deductions.
    Expects a POST request with employeeid in URL and data in body.
    """
    # CHANGE THIS LINE: Ensure the parameter name here is 'employee_id'
    def post(self, request, employee_id, format=None): # <-- THIS LINE WAS CHANGED
        # Use employeeid=employee_id for the lookup as employeeid is the actual field on your model
        employee = get_object_or_404(Employees, employeeid=employee_id)

        serializer = EmployeePayslipSerializer(employee, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
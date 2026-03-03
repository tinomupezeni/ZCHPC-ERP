from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from payroll.payroll_models import Payroll
from ..serializers.payslip_serializers import (
    PortalPayslipListSerializer,
    PortalPayslipDetailSerializer,
    PayslipYearSummarySerializer,
)


class PayslipListView(APIView):
    """List employee's payslips"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )
        year = request.query_params.get('year')

        # Only show processed or paid payslips to employees
        queryset = Payroll.objects.filter(
            employee=employee,
            status__in=['Processed', 'Paid']
        ).order_by('-period')

        if year:
            queryset = queryset.filter(period__year=year)

        serializer = PortalPayslipListSerializer(queryset, many=True)

        # Get available years for filtering
        years = Payroll.objects.filter(
            employee=employee,
            status__in=['Processed', 'Paid']
        ).dates('period', 'year', order='DESC')
        available_years = [d.year for d in years]

        return Response({
            'payslips': serializer.data,
            'available_years': available_years,
            'current_year': year or timezone.now().year,
        })


class PayslipDetailView(APIView):
    """Get detailed payslip information"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            payslip = Payroll.objects.get(
                pk=pk,
                employee=employee,
                status__in=['Processed', 'Paid']
            )
        except Payroll.DoesNotExist:
            return Response(
                {'detail': 'Payslip not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PortalPayslipDetailSerializer(payslip)
        return Response(serializer.data)


class PayslipYearSummaryView(APIView):
    """Get yearly payslip summary"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )
        year = request.query_params.get('year', timezone.now().year)

        payslips = Payroll.objects.filter(
            employee=employee,
            period__year=year,
            status__in=['Processed', 'Paid']
        )

        if not payslips.exists():
            return Response({
                'year': int(year),
                'total_gross_usd': 0,
                'total_gross_zig': 0,
                'total_deductions_usd': 0,
                'total_deductions_zig': 0,
                'total_net_usd': 0,
                'total_net_zig': 0,
                'payslip_count': 0,
            })

        # Calculate aggregates
        aggregates = payslips.aggregate(
            total_base_usd=Sum('base_salary_usd'),
            total_base_zig=Sum('base_salary_zig'),
            total_allowances_usd=Sum('total_allowances_usd'),
            total_allowances_zig=Sum('total_allowances_zig'),
            total_deductions_usd=Sum('total_deductions_usd'),
            total_deductions_zig=Sum('total_deductions_zig'),
            total_net_usd=Sum('net_salary_usd'),
            total_net_zig=Sum('net_salary_zig'),
        )

        data = {
            'year': int(year),
            'total_gross_usd': (aggregates['total_base_usd'] or 0) + (aggregates['total_allowances_usd'] or 0),
            'total_gross_zig': (aggregates['total_base_zig'] or 0) + (aggregates['total_allowances_zig'] or 0),
            'total_deductions_usd': aggregates['total_deductions_usd'] or 0,
            'total_deductions_zig': aggregates['total_deductions_zig'] or 0,
            'total_net_usd': aggregates['total_net_usd'] or 0,
            'total_net_zig': aggregates['total_net_zig'] or 0,
            'payslip_count': payslips.count(),
        }

        serializer = PayslipYearSummarySerializer(data)
        return Response(serializer.data)


class PayslipDownloadView(APIView):
    """Download payslip as PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            return Response(
                {'detail': 'No employee profile found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            payslip = Payroll.objects.get(
                pk=pk,
                employee=employee,
                status__in=['Processed', 'Paid']
            )
        except Payroll.DoesNotExist:
            return Response(
                {'detail': 'Payslip not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # For now, return a simple text response
        # In production, you would generate a proper PDF using reportlab or weasyprint
        content = f"""
PAYSLIP
========================================
Employee: {payslip.employee.first_name} {payslip.employee.surname}
Employee ID: {payslip.employee.employee_id}
Period: {payslip.period.strftime('%B %Y')}
========================================

EARNINGS (USD)
--------------
Base Salary:     ${payslip.base_salary_usd:,.2f}
Allowances:      ${payslip.total_allowances_usd:,.2f}
----------------------------------------
Gross Salary:    ${float(payslip.base_salary_usd) + float(payslip.total_allowances_usd):,.2f}

DEDUCTIONS (USD)
----------------
PAYE:            ${payslip.paye_usd:,.2f}
AIDS Levy:       ${payslip.aids_levy_usd:,.2f}
NSSA (Employee): ${payslip.nssa_employee_usd:,.2f}
----------------------------------------
Total Deductions: ${payslip.total_deductions_usd:,.2f}

========================================
NET SALARY (USD): ${payslip.net_salary_usd:,.2f}
NET SALARY (ZiG): ZiG {payslip.net_salary_zig:,.2f}
========================================
Exchange Rate: {payslip.exchange_rate}
"""

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.period.strftime("%Y_%m")}.txt"'
        return response

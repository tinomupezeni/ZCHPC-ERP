# human_resources/views/report_views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count, F
from django.utils import timezone
from ..hr_models import LeaveBalance, Employees, TrainingEnrollment
from payroll.payroll_models import Payroll


class ReportBaseViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]


class LeaveBalanceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns leave balances for all employees.
    """
    queryset = LeaveBalance.objects.all().select_related('employee', 'leave_type')
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Filter by year if provided
        year = request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        else:
            queryset = queryset.filter(year=timezone.now().year)

        data = []
        for item in queryset:
            data.append({
                "id": item.id,
                "employee_name": f"{item.employee.first_name} {item.employee.surname}",
                "employee_id": item.employee.employee_id,
                "department": item.employee.department.name if item.employee.department else "N/A",
                "leave_type": item.leave_type.name,
                "days_entitled": item.employee.leave_days_entitled or 0,
                "days_remaining": float(item.days_remaining),
                "days_used": float((item.employee.leave_days_entitled or 0) - item.days_remaining),
                "year": item.year
            })
        return Response(data)


class PayrollReportViewSet(ReportBaseViewSet):
    """
    Handlers for Financial Reports based on the Payroll model.
    """

    def get_payroll_queryset(self, request):
        """Helper to get filtered payroll queryset"""
        queryset = Payroll.objects.all().select_related('employee', 'employee__department')

        # Filter by period/month
        period = request.query_params.get('period')
        if period:
            queryset = queryset.filter(period=period)

        # Filter by status
        status = request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by department
        department_id = request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)

        return queryset

    def list(self, request):
        """
        GET /api/hr/reports/basic-salary/
        Basic Salary Report
        """
        payrolls = self.get_payroll_queryset(request)
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employee_name": f"{p.employee.first_name} {p.employee.surname}",
                "employee_id": p.employee.employee_id,
                "department": p.employee.department.name if p.employee.department else "N/A",
                "period": p.period.strftime('%B %Y'),
                "base_salary_usd": float(p.base_salary_usd),
                "base_salary_zig": float(p.base_salary_zig),
                "net_salary_usd": float(p.net_salary_usd),
                "net_salary_zig": float(p.net_salary_zig),
                "status": p.status
            })
        return Response(data)

    def paye(self, request):
        """
        GET /api/hr/reports/paye/
        PAYE Tax Report
        """
        payrolls = self.get_payroll_queryset(request)
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employee_name": f"{p.employee.first_name} {p.employee.surname}",
                "employee_id": p.employee.employee_id,
                "department": p.employee.department.name if p.employee.department else "N/A",
                "period": p.period.strftime('%B %Y'),
                "gross_salary_usd": float(p.base_salary_usd),
                "paye_usd": float(p.paye_usd),
                "paye_zig": float(p.paye_zig),
                "aids_levy_usd": float(p.aids_levy_usd),
                "aids_levy_zig": float(p.aids_levy_zig),
            })
        return Response(data)

    def nssa(self, request):
        """
        GET /api/hr/reports/nssa/
        NSSA Contributions Report
        """
        payrolls = self.get_payroll_queryset(request)
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employee_name": f"{p.employee.first_name} {p.employee.surname}",
                "employee_id": p.employee.employee_id,
                "nssa_number": p.employee.nssa_number or "N/A",
                "department": p.employee.department.name if p.employee.department else "N/A",
                "period": p.period.strftime('%B %Y'),
                "gross_salary_usd": float(p.base_salary_usd),
                "employee_contribution_usd": float(p.nssa_employee_usd),
                "employer_contribution_usd": float(p.nssa_employer_usd),
                "total_nssa_usd": float(p.nssa_employee_usd + p.nssa_employer_usd),
                "employee_contribution_zig": float(p.nssa_employee_zig),
                "employer_contribution_zig": float(p.nssa_employer_zig),
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def allowances(self, request):
        """
        GET /api/hr/reports/allowances/
        Allowances Report
        """
        payrolls = self.get_payroll_queryset(request)
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employee_name": f"{p.employee.first_name} {p.employee.surname}",
                "employee_id": p.employee.employee_id,
                "department": p.employee.department.name if p.employee.department else "N/A",
                "period": p.period.strftime('%B %Y'),
                "base_salary_usd": float(p.base_salary_usd),
                "total_allowances_usd": float(p.total_allowances_usd),
                "total_allowances_zig": float(p.total_allowances_zig),
                "gross_salary_usd": float(p.base_salary_usd + p.total_allowances_usd),
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def deductions(self, request):
        """
        GET /api/hr/reports/deductions/
        Deductions Report
        """
        payrolls = self.get_payroll_queryset(request)
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employee_name": f"{p.employee.first_name} {p.employee.surname}",
                "employee_id": p.employee.employee_id,
                "department": p.employee.department.name if p.employee.department else "N/A",
                "period": p.period.strftime('%B %Y'),
                "gross_salary_usd": float(p.base_salary_usd + p.total_allowances_usd),
                "paye_usd": float(p.paye_usd),
                "nssa_usd": float(p.nssa_employee_usd),
                "aids_levy_usd": float(p.aids_levy_usd),
                "other_deductions_usd": float(p.total_deductions_usd),
                "total_deductions_usd": float(p.paye_usd + p.nssa_employee_usd + p.aids_levy_usd + p.total_deductions_usd),
                "net_salary_usd": float(p.net_salary_usd),
            })
        return Response(data)


class EmployeeReportViewSet(ReportBaseViewSet):
    """
    Employee-based HR reports
    """

    def list(self, request):
        """
        GET /api/hr/reports/employees/
        Employee Headcount Report
        """
        employees = Employees.objects.filter(is_active=True).select_related('department', 'position')

        # Filter by department
        department_id = request.query_params.get('department')
        if department_id:
            employees = employees.filter(department_id=department_id)

        data = []
        for emp in employees:
            data.append({
                "id": emp.id,
                "employee_id": emp.employee_id,
                "employee_name": f"{emp.first_name} {emp.surname}",
                "department": emp.department.name if emp.department else "N/A",
                "position": emp.position.title if emp.position else "N/A",
                "employee_type": emp.employee_type,
                "date_joined": emp.date_joined.strftime('%Y-%m-%d') if emp.date_joined else "N/A",
                "email": emp.email,
                "phone": emp.phone or "N/A",
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def training(self, request):
        """
        GET /api/hr/reports/employees/training/
        Training Report
        """
        enrollments = TrainingEnrollment.objects.all().select_related(
            'employee', 'employee__department', 'session', 'session__program'
        )

        # Filter by department
        department_id = request.query_params.get('department')
        if department_id:
            enrollments = enrollments.filter(employee__department_id=department_id)

        data = []
        for e in enrollments:
            data.append({
                "id": e.id,
                "employee_name": f"{e.employee.first_name} {e.employee.surname}",
                "employee_id": e.employee.employee_id,
                "department": e.employee.department.name if e.employee.department else "N/A",
                "program": e.session.program.name if e.session and e.session.program else "N/A",
                "session": e.session.name if e.session else "N/A",
                "status": e.status,
                "enrolled_on": e.enrolled_on.strftime('%Y-%m-%d') if e.enrolled_on else "N/A",
                "completed_on": e.completed_on.strftime('%Y-%m-%d') if e.completed_on else "N/A",
            })
        return Response(data)


class SummaryReportViewSet(ReportBaseViewSet):
    """
    Summary/Dashboard reports with aggregated data
    """

    def list(self, request):
        """
        GET /api/hr/reports/summary/
        Returns summary statistics for dashboard
        """
        # Get current period
        current_period = request.query_params.get('period')

        # Employee stats
        total_employees = Employees.objects.filter(is_active=True).count()

        # Payroll stats for the period
        payroll_qs = Payroll.objects.all()
        if current_period:
            payroll_qs = payroll_qs.filter(period=current_period)

        payroll_stats = payroll_qs.aggregate(
            total_base_usd=Sum('base_salary_usd'),
            total_net_usd=Sum('net_salary_usd'),
            total_paye_usd=Sum('paye_usd'),
            total_nssa_usd=Sum(F('nssa_employee_usd') + F('nssa_employer_usd')),
            total_allowances_usd=Sum('total_allowances_usd'),
            total_deductions_usd=Sum('total_deductions_usd'),
            record_count=Count('id'),
        )

        return Response({
            "total_employees": total_employees,
            "payroll_records": payroll_stats['record_count'] or 0,
            "total_gross_salary_usd": float(payroll_stats['total_base_usd'] or 0),
            "total_net_salary_usd": float(payroll_stats['total_net_usd'] or 0),
            "total_paye_usd": float(payroll_stats['total_paye_usd'] or 0),
            "total_nssa_usd": float(payroll_stats['total_nssa_usd'] or 0),
            "total_allowances_usd": float(payroll_stats['total_allowances_usd'] or 0),
            "total_deductions_usd": float(payroll_stats['total_deductions_usd'] or 0),
        })

# human_resources/views/report_views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from ..hr_models import LeaveBalance
from payroll.payroll_models import Payroll # Assuming this exists based on your snippet

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
        data = []
        for item in queryset:
            data.append({
                "id": item.id,
                "employeeName": f"{item.employee.first_name} {item.employee.surname}",
                "employeeId": item.employee.employee_id,
                "leaveType": item.leave_type.name,
                "daysRemaining": item.days_remaining,
                "year": item.year
            })
        return Response(data)

class PayrollReportViewSet(ReportBaseViewSet):
    """
    Handlers for Financial Reports based on the Payroll model.
    """
    def list(self, request):
        # Default to Basic Salary view
        payrolls = Payroll.objects.all().select_related('employee')
        data = []
        for p in payrolls:
            data.append({
                "id": p.id,
                "employeeName": f"{p.employee.first_name} {p.employee.surname}",
                "period": p.period,
                "amount_usd": p.base_salary_usd,
                "amount_zig": p.base_salary_zig,
                "status": p.status
            })
        return Response(data)

    # Custom actions for specific report types to keep URL structure clean
    # GET /api/reports/payroll/paye/
    def paye(self, request):
        payrolls = Payroll.objects.all().select_related('employee')
        data = [{
            "id": p.id,
            "employeeName": f"{p.employee.first_name} {p.employee.surname}",
            "period": p.period,
            "paye_usd": p.paye_usd,
            "paye_zig": p.paye_zig
        } for p in payrolls]
        return Response(data)

    # GET /api/reports/payroll/nssa/
    def nssa(self, request):
        payrolls = Payroll.objects.all().select_related('employee')
        data = [{
            "id": p.id,
            "employeeName": f"{p.employee.first_name} {p.employee.surname}",
            "period": p.period,
            "nssa_usd": p.nssa_employee_usd,
            "nssa_zig": p.nssa_employee_zig
        } for p in payrolls]
        return Response(data)
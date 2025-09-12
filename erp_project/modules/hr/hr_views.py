from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from erp.models import Payroll, Employees, EmployeeDeductables
from .serializers.reports_serializers import PayrollSerializer, EmployeeSerializer

class PayrollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payroll.objects.all().select_related('employee')
    serializer_class = PayrollSerializer

class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Employees.objects.all()
    serializer_class = EmployeeSerializer

class PAYEReportViewSet(viewsets.ViewSet):
    def list(self, request):
        payrolls = Payroll.objects.all().select_related('employee')
        data = [
            {
                'employee': {
                    'employeeid': p.employee.employeeid,
                    'firstname': p.employee.firstname,
                    'surname': p.employee.surname
                },
                'gross_income_usd': p.base_salary_usd,
                'paye_amount_usd': p.paye_usd,
                'gross_income_zig': p.base_salary_zig,
                'paye_amount_zig': p.paye_zig
            }
            for p in payrolls
        ]
        return Response(data)

class NSSAReportViewSet(viewsets.ViewSet):
    def list(self, request):
        payrolls = Payroll.objects.all().select_related('employee')
        data = [
            {
                'employee': {
                    'employeeid': p.employee.employeeid,
                    'firstname': p.employee.firstname,
                    'surname': p.employee.surname
                },
                'period': p.period,
                'nssa_contribution_usd': p.nssa_employee_usd,
                'nssa_contribution_zig': p.nssa_employee_zig
            }
            for p in payrolls
        ]
        return Response(data)

class AllowanceReportViewSet(viewsets.ViewSet):
    def list(self, request):
        records = EmployeeDeductables.objects.filter(active=True).select_related('employee', 'pension_fund', 'medical_aid')
        data = [
            {
                'employee': {
                    'employeeid': r.employee.employeeid,
                    'firstname': r.employee.firstname,
                    'surname': r.employee.surname
                },
                'period': r.effective_date,
                'description': r.pension_fund.name if r.pension_fund else "N/A",
                'amount_usd': r.pension_fund.employee_rate if r.pension_fund else 0,
                'amount_zig': r.pension_fund.employee_rate if r.pension_fund else 0,
            }
            for r in records
        ]
        return Response(data)

class DeductionReportViewSet(viewsets.ViewSet):
    def list(self, request):
        records = EmployeeDeductables.objects.filter(active=True).select_related('employee', 'medical_aid')
        data = [
            {
                'employee': {
                    'employeeid': r.employee.employeeid,
                    'firstname': r.employee.firstname,
                    'surname': r.employee.surname
                },
                'period': r.effective_date,
                'description': r.medical_aid.name if r.medical_aid else "N/A",
                'amount_usd': r.medical_aid.usd_amount if r.medical_aid else 0,
                'amount_zig': r.medical_aid.zwl_amount if r.medical_aid else 0,
            }
            for r in records
        ]
        return Response(data)

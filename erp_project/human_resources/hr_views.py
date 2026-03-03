from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .hr_models import DeductionType, EmployeeDeduction, EmployeeAllowance, AllowanceType, Employees, EmployeePayrollConfig
from payroll.payroll_models import Payroll
from .serializers.reports_serializers import DeductionTypeSerializer, PayrollSerializer, EmployeeSerializer

class PayrollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payroll.objects.all().select_related('employee')
    serializer_class = PayrollSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employees.objects.all()
    serializer_class = EmployeeSerializer

    @action(detail=True, methods=['post', 'put'])
    def deductions(self, request, pk=None):
        """
        POST/PUT /api/hr/employees/{id}/deductions/
        Update employee deductions.
        Payload: { "deductions": [{"deduction_type_id": 1, "amount": 100, "currency": "USD"}, ...] }
        """
        try:
            employee = self.get_object()
            deductions_data = request.data.get('deductions', [])

            with transaction.atomic():
                # Clear existing deductions and recreate
                EmployeeDeduction.objects.filter(employee=employee).delete()

                for item in deductions_data:
                    deduction_type_id = item.get('deduction_type_id') or item.get('id')
                    if deduction_type_id:
                        try:
                            deduction_type = DeductionType.objects.get(pk=deduction_type_id)
                            EmployeeDeduction.objects.create(
                                employee=employee,
                                deduction_type=deduction_type,
                                amount=item.get('amount', 0),
                                currency=item.get('currency', 'USD')
                            )
                        except DeductionType.DoesNotExist:
                            continue

            # Return updated deductions
            updated_deductions = EmployeeDeduction.objects.filter(employee=employee)
            deductions_list = [
                {
                    'id': d.id,
                    'deduction_type_id': d.deduction_type.id,
                    'name': d.deduction_type.name,
                    'amount': float(d.amount),
                    'currency': d.currency
                }
                for d in updated_deductions
            ]

            return Response({
                'message': 'Deductions updated successfully',
                'deductions': deductions_list
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'put'])
    def allowances(self, request, pk=None):
        """
        POST/PUT /api/hr/employees/{id}/allowances/
        Update employee allowances.
        Payload: { "allowances": [{"allowance_type_id": 1, "amount": 100, "currency": "USD"}, ...] }
        """
        try:
            employee = self.get_object()
            allowances_data = request.data.get('allowances', [])

            with transaction.atomic():
                # Clear existing allowances and recreate
                EmployeeAllowance.objects.filter(employee=employee).delete()

                for item in allowances_data:
                    allowance_type_id = item.get('allowance_type_id') or item.get('id')
                    if allowance_type_id:
                        try:
                            allowance_type = AllowanceType.objects.get(pk=allowance_type_id)
                            EmployeeAllowance.objects.create(
                                employee=employee,
                                allowance_type=allowance_type,
                                amount=item.get('amount', 0),
                                currency=item.get('currency', 'USD')
                            )
                        except AllowanceType.DoesNotExist:
                            continue

            # Return updated allowances
            updated_allowances = EmployeeAllowance.objects.filter(employee=employee)
            allowances_list = [
                {
                    'id': a.id,
                    'allowance_type_id': a.allowance_type.id,
                    'name': a.allowance_type.name,
                    'amount': float(a.amount),
                    'currency': a.currency
                }
                for a in updated_allowances
            ]

            return Response({
                'message': 'Allowances updated successfully',
                'allowances': allowances_list
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        records = EmployeePayrollConfig.objects.filter(active=True).select_related('employee', 'pension_fund', 'medical_aid')
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

class DeductionTypeViewSet(viewsets.ModelViewSet):
    """
    Manage Tax and Deduction Categories (e.g., NSSA, PAYE, Medical Aid)
    """
    queryset = DeductionType.objects.all()
    serializer_class = DeductionTypeSerializer
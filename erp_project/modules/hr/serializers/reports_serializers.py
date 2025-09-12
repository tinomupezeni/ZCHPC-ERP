from rest_framework import serializers
from erp.models import Payroll, Employees, EmployeeDeductables, AllowanceType, DeductionType

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = ['employeeid', 'firstname', 'surname', 'email']

class PayrollSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    
    class Meta:
        model = Payroll
        fields = [
            'employee', 'period', 'base_salary_usd', 'base_salary_zig',
            'net_salary_usd', 'net_salary_zig', 'paye_usd', 'paye_zig',
            'nssa_employee_usd', 'nssa_employee_zig',
            'total_allowances_usd', 'total_allowances_zig',
            'total_deductions_usd', 'total_deductions_zig',
            'status'
        ]

class AllowanceSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    
    class Meta:
        model = AllowanceType
        fields = ['name', 'description', 'amount']

class DeductionSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    
    class Meta:
        model = DeductionType
        fields = ['name', 'description', 'amount']

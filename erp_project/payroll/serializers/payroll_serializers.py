# erp/app_serializers/payroll_serializer.py
from rest_framework import serializers
from ..payroll_models import Payroll, DailyZiGRateToUSD, PayrollPeriod

class PayrollSerializer(serializers.ModelSerializer):
    # Flatten employee details for easier display in the frontend table
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_first_name = serializers.CharField(source='employee.first_name', read_only=True)
    employee_surname = serializers.CharField(source='employee.surname', read_only=True)
    employee_name = serializers.SerializerMethodField() # Full Name
    
    # Handle relations safely (return "N/A" if null)
    employee_department = serializers.CharField(source='employee.department.name', default="N/A", read_only=True)
    employee_position = serializers.CharField(source='employee.position.title', default="N/A", read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id',
            'employee_id',
            'employee_first_name', # New
            'employee_surname',    # New
            'employee_name',       # Full Name helper
            'employee_department',
            'employee_position',   # New
            'period',
            'status',
            # Financials
            'base_salary_usd', 'base_salary_zig',
            'net_salary_usd', 'net_salary_zig',
            'paye_usd', 'paye_zig',
            'nssa_employee_usd', 'nssa_employee_zig',
            'total_allowances_usd', 'total_deductions_usd'
        ]

    def get_employee_name(self, obj):
        if obj.employee:
            return f"{obj.employee.first_name} {obj.employee.surname}"
        return "Unknown"
class DailyZiGRateToUSDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyZiGRateToUSD
        fields = ["id", "date", "average"]

class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = "__all__"

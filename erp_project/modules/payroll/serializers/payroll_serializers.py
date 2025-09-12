# erp/app_serializers/payroll_serializer.py
from rest_framework import serializers
from erp.models import Payroll, DailyZiGRateToUSD, PayrollPeriod, AllowanceType, DeductionType

class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.firstname", read_only=True)
    employee_surname = serializers.CharField(source="employee.surname", read_only=True)
    employee_id = serializers.CharField(source="employee.employeeid", read_only=True)
    employee_department = serializers.CharField(source="employee.department", read_only=True)

    class Meta:
        model = Payroll
        fields = "__all__"
        read_only_fields = ["net_salary_usd", "net_salary_zig", "exchange_rate", "created_at"]
        extra_kwargs = {
            "employee": {"write_only": True}
        }

class DailyZiGRateToUSDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyZiGRateToUSD
        fields = ["id", "date", "average"]

class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = "__all__"

class AllowanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowanceType
        fields = "__all__"

class DeductionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeductionType
        fields = "__all__"

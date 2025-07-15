from rest_framework import serializers
from ..models import (
    Employees, Payroll, ZiGRateToUSD, NSSACap, PensionFund,
    EmployeeDeductables, TaxBracket
)

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = '__all__'

class ZiGRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZiGRateToUSD
        fields = '__all__'

class NSSACapSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSSACap
        fields = '__all__'

class PensionFundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PensionFund
        fields = '__all__'

class EmployeeDeductablesSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    pension_fund = PensionFundSerializer(read_only=True)

    class Meta:
        model = EmployeeDeductables
        fields = '__all__'

class TaxBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxBracket
        fields = '__all__'

class PayrollSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True) # Nested serializer for employee details

    class Meta:
        model = Payroll
        fields = '__all__'
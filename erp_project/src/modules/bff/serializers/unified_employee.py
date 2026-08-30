from rest_framework import serializers

class UnifiedEmployeeProfileSerializer(serializers.Serializer):
    # Base HR Info
    uuid = serializers.UUIDField()
    employee_id = serializers.CharField()
    first_name = serializers.CharField()
    surname = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    
    # Nested Payroll Info
    usd_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    zig_salary = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    pay_frequency = serializers.CharField(allow_null=True)
    
    # Banking Info
    bank_name = serializers.CharField(allow_null=True)
    bank_account = serializers.CharField(allow_null=True)
    
    # Statutory Info
    nssa_number = serializers.CharField(allow_null=True)
    zimra_tax_number = serializers.CharField(allow_null=True)
    paye_number = serializers.CharField(allow_null=True)

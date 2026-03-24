"""
Employee API serializers.
"""

from rest_framework import serializers


class EmployeeResponseSerializer(serializers.Serializer):
    """Serializer for employee response data."""

    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    surname = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_null=True)
    phone = serializers.CharField(read_only=True, allow_null=True)
    national_id = serializers.CharField(read_only=True, allow_null=True)
    date_of_birth = serializers.DateField(read_only=True, allow_null=True)
    gender = serializers.CharField(read_only=True, allow_null=True)
    marital_status = serializers.CharField(read_only=True, allow_null=True)
    department_id = serializers.IntegerField(read_only=True, allow_null=True)
    department_name = serializers.CharField(read_only=True, allow_null=True)
    position_id = serializers.IntegerField(read_only=True, allow_null=True)
    position_title = serializers.CharField(read_only=True, allow_null=True)
    employee_type = serializers.CharField(read_only=True)
    date_joined = serializers.DateField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    usd_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    zig_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, allow_null=True
    )
    pay_frequency = serializers.CharField(read_only=True)


class CreateEmployeeRequestSerializer(serializers.Serializer):
    """Serializer for creating a new employee."""

    first_name = serializers.CharField(max_length=100)
    surname = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    national_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=["Male", "Female", "Other"],
        required=False,
        allow_blank=True,
    )
    marital_status = serializers.ChoiceField(
        choices=["Single", "Married", "Divorced", "Widowed"],
        required=False,
        allow_blank=True,
    )
    department_id = serializers.IntegerField(required=False, allow_null=True)
    position_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    employee_type = serializers.ChoiceField(
        choices=["Full-time", "Part-time", "Contract", "Intern"],
        default="Full-time",
    )
    reports_to_id = serializers.IntegerField(required=False, allow_null=True)
    date_joined = serializers.DateField(required=False, allow_null=True)
    contract_from = serializers.DateField(required=False, allow_null=True)
    contract_to = serializers.DateField(required=False, allow_null=True)
    usd_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    zig_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    pay_frequency = serializers.ChoiceField(
        choices=["Monthly", "Weekly", "Bi-Weekly"],
        default="Monthly",
    )
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    bank_account = serializers.CharField(max_length=50, required=False, allow_blank=True)
    nssa_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    zimra_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    paye_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    pays_aids_levy = serializers.BooleanField(default=True)
    pension_fund = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    emergency_contact_relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)


class UpdateEmployeeRequestSerializer(serializers.Serializer):
    """Serializer for updating an employee."""

    first_name = serializers.CharField(max_length=100, required=False)
    surname = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=["Male", "Female", "Other"],
        required=False,
        allow_blank=True,
    )
    marital_status = serializers.ChoiceField(
        choices=["Single", "Married", "Divorced", "Widowed"],
        required=False,
        allow_blank=True,
    )
    department_id = serializers.IntegerField(required=False, allow_null=True)
    position_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    employee_type = serializers.ChoiceField(
        choices=["Full-time", "Part-time", "Contract", "Intern"],
        required=False,
    )
    reports_to_id = serializers.IntegerField(required=False, allow_null=True)
    contract_from = serializers.DateField(required=False, allow_null=True)
    contract_to = serializers.DateField(required=False, allow_null=True)
    usd_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    zig_salary = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    pay_frequency = serializers.ChoiceField(
        choices=["Monthly", "Weekly", "Bi-Weekly"],
        required=False,
    )
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    bank_account = serializers.CharField(max_length=50, required=False, allow_blank=True)
    nssa_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    zimra_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    paye_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    pays_aids_levy = serializers.BooleanField(required=False)
    pension_fund = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    emergency_contact_relationship = serializers.CharField(max_length=50, required=False, allow_blank=True)


class EmployeeListItemSerializer(serializers.Serializer):
    """Serializer for employee list items (minimal data)."""

    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    surname = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_null=True)
    department_name = serializers.CharField(read_only=True, allow_null=True)
    position_title = serializers.CharField(read_only=True, allow_null=True)
    is_active = serializers.BooleanField(read_only=True)


class SalarySerializer(serializers.Serializer):
    """Serializer for salary information."""

    employee_id = serializers.IntegerField(read_only=True)
    employee_number = serializers.CharField(read_only=True)
    usd_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    zig_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    pay_frequency = serializers.CharField(read_only=True)

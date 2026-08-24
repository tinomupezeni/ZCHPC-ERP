"""
Payroll API serializers.
"""

from decimal import Decimal
from rest_framework import serializers


class TaxBracketSerializer(serializers.Serializer):
    """Serializer for tax bracket."""

    id = serializers.IntegerField(read_only=True)
    currency = serializers.CharField()
    min_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_income = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    deduction = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_from = serializers.DateField()


class CreateTaxBracketSerializer(serializers.Serializer):
    """Serializer for creating tax brackets."""

    currency = serializers.ChoiceField(choices=["USD", "ZIG"])
    min_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_income = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True, required=False
    )
    rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    deduction = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_from = serializers.DateField()
    provider = serializers.CharField(max_length=100, required=False, allow_blank=True)


class ExchangeRateSerializer(serializers.Serializer):
    """Serializer for exchange rate."""

    id = serializers.IntegerField(read_only=True)
    rate_date = serializers.DateField(source="date")
    zig_to_usd_rate = serializers.DecimalField(
        max_digits=20, decimal_places=8, source="average"
    )
    usd_to_zig_rate = serializers.SerializerMethodField()
    source = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)

    def get_usd_to_zig_rate(self, obj):
        """Calculate inverse rate."""
        if hasattr(obj, "average") and obj.average:
            return str((Decimal("1") / obj.average).quantize(Decimal("0.00000001")))
        if hasattr(obj, "zig_to_usd_rate") and obj.zig_to_usd_rate:
            return str((Decimal("1") / obj.zig_to_usd_rate).quantize(Decimal("0.00000001")))
        return None


class CreateExchangeRateSerializer(serializers.Serializer):
    """Serializer for creating exchange rate."""

    date = serializers.DateField()
    zigRate = serializers.DecimalField(max_digits=20, decimal_places=8)


class PayslipSerializer(serializers.Serializer):
    """Serializer for payslip."""

    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.IntegerField()
    employee_name = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()

    # Base salary
    base_salary_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    base_salary_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Gross
    gross_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    gross_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Allowances
    total_allowances_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_allowances_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Statutory deductions
    paye_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    paye_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    aids_levy_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    aids_levy_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    nssa_employee_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    nssa_employee_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    nssa_employer_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    nssa_employer_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Other deductions
    other_deductions_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    other_deductions_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Totals
    total_deductions_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deductions_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_zig = serializers.DecimalField(max_digits=12, decimal_places=2)

    exchange_rate = serializers.DecimalField(max_digits=10, decimal_places=4)
    status = serializers.CharField()

    def get_employee_name(self, obj):
        """Get employee name from related model."""
        if hasattr(obj, "employee") and obj.employee:
            return f"{obj.employee.first_name} {obj.employee.surname}"
        return "Unknown"

    def get_period(self, obj):
        """Get period as string."""
        if hasattr(obj, "period"):
            if hasattr(obj.period, "code"):
                return obj.period.code
            return f"{obj.period.year}-{obj.period.month:02d}"
        return None


class PayslipListSerializer(serializers.Serializer):
    """Simplified serializer for payslip lists."""

    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.CharField(source="employee.employee_id")
    employee_name = serializers.SerializerMethodField()
    department = serializers.CharField(
        source="employee.department.name", default="N/A"
    )
    period = serializers.SerializerMethodField()
    gross_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    gross_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_salary_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.CharField()

    def get_employee_name(self, obj):
        """Get employee name."""
        if hasattr(obj, "employee") and obj.employee:
            return f"{obj.employee.first_name} {obj.employee.surname}"
        return "Unknown"

    def get_period(self, obj):
        """Get period as string."""
        if hasattr(obj, "period"):
            if hasattr(obj.period, "year") and hasattr(obj.period, "month"):
                return f"{obj.period.year}-{obj.period.month:02d}"
        return None


class ProcessPayrollSerializer(serializers.Serializer):
    """Serializer for process payroll request."""

    month = serializers.CharField(help_text="Period in YYYY-MM format")


class PayrollSummarySerializer(serializers.Serializer):
    """Serializer for payroll summary."""

    period = serializers.CharField()
    total_employees = serializers.IntegerField()
    total_gross_usd = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_gross_zig = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_net_usd = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_net_zig = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paye_usd = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_paye_zig = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_nssa_usd = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_nssa_zig = serializers.DecimalField(max_digits=14, decimal_places=2)
    status = serializers.CharField()


class AllowanceTypeSerializer(serializers.Serializer):
    """Serializer for allowance type."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_blank=True, required=False)
    default_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )


class DeductionTypeSerializer(serializers.Serializer):
    """Serializer for deduction type."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_blank=True, required=False)
    default_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

class EmployeeBankAccountSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bank_name = serializers.CharField(max_length=100)
    branch_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    account_number = serializers.CharField(max_length=50)
    currency = serializers.CharField(max_length=10, default='USD')
    is_primary = serializers.BooleanField(default=True)

class StatutoryProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nssa_number = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    zimra_tax_number = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    paye_number = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    pays_aids_levy = serializers.BooleanField(default=True)
    pension_fund = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

class PayrollProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    employee_uuid = serializers.UUIDField(source='employee.uuid', read_only=True)
    usd_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    zig_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    pay_frequency = serializers.CharField(max_length=20, required=False)

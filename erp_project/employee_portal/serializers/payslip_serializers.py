from rest_framework import serializers
from payroll.payroll_models import Payroll


class PortalPayslipListSerializer(serializers.ModelSerializer):
    """Serializer for listing employee payslips (summary view)"""
    period_display = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            'id',
            'period',
            'period_display',
            'month',
            'year',
            'status',
            'base_salary_usd',
            'net_salary_usd',
            'base_salary_zig',
            'net_salary_zig',
            'exchange_rate',
        ]

    def get_period_display(self, obj):
        return obj.period.strftime('%B %Y')

    def get_month(self, obj):
        return obj.period.month

    def get_year(self, obj):
        return obj.period.year


class PortalPayslipDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payslip view"""
    period_display = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    department = serializers.CharField(source='employee.department.name', default='N/A', read_only=True)
    position = serializers.CharField(source='employee.position.title', default='N/A', read_only=True)

    # Earnings breakdown
    earnings = serializers.SerializerMethodField()
    # Deductions breakdown
    deductions = serializers.SerializerMethodField()
    # Summary
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            'id',
            'period',
            'period_display',
            'month',
            'year',
            'status',
            'employee_name',
            'employee_id',
            'department',
            'position',
            'exchange_rate',
            'earnings',
            'deductions',
            'summary',
            'notes',
            'created_at',
        ]

    def get_period_display(self, obj):
        return obj.period.strftime('%B %Y')

    def get_month(self, obj):
        return obj.period.month

    def get_year(self, obj):
        return obj.period.year

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.surname}"

    def get_earnings(self, obj):
        """Return earnings breakdown"""
        return {
            'base_salary': {
                'usd': float(obj.base_salary_usd),
                'zig': float(obj.base_salary_zig),
            },
            'allowances': {
                'usd': float(obj.total_allowances_usd),
                'zig': float(obj.total_allowances_zig),
            },
            'gross': {
                'usd': float(obj.base_salary_usd) + float(obj.total_allowances_usd),
                'zig': float(obj.base_salary_zig) + float(obj.total_allowances_zig),
            },
        }

    def get_deductions(self, obj):
        """Return deductions breakdown"""
        return {
            'paye': {
                'usd': float(obj.paye_usd),
                'zig': float(obj.paye_zig),
            },
            'aids_levy': {
                'usd': float(obj.aids_levy_usd),
                'zig': float(obj.aids_levy_zig),
            },
            'nssa_employee': {
                'usd': float(obj.nssa_employee_usd),
                'zig': float(obj.nssa_employee_zig),
            },
            'other_deductions': {
                'usd': float(obj.total_deductions_usd) - float(obj.paye_usd) - float(obj.aids_levy_usd) - float(obj.nssa_employee_usd),
                'zig': float(obj.total_deductions_zig) - float(obj.paye_zig) - float(obj.aids_levy_zig) - float(obj.nssa_employee_zig),
            },
            'total': {
                'usd': float(obj.total_deductions_usd),
                'zig': float(obj.total_deductions_zig),
            },
        }

    def get_summary(self, obj):
        """Return payslip summary"""
        gross_usd = float(obj.base_salary_usd) + float(obj.total_allowances_usd)
        gross_zig = float(obj.base_salary_zig) + float(obj.total_allowances_zig)

        return {
            'gross_salary': {
                'usd': gross_usd,
                'zig': gross_zig,
            },
            'total_deductions': {
                'usd': float(obj.total_deductions_usd),
                'zig': float(obj.total_deductions_zig),
            },
            'net_salary': {
                'usd': float(obj.net_salary_usd),
                'zig': float(obj.net_salary_zig),
            },
        }


class PayslipYearSummarySerializer(serializers.Serializer):
    """Serializer for yearly payslip summary"""
    year = serializers.IntegerField()
    total_gross_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_gross_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deductions_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_deductions_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_net_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_net_zig = serializers.DecimalField(max_digits=12, decimal_places=2)
    payslip_count = serializers.IntegerField()

# erp/app_serializers/payroll_serializer.py
from rest_framework import serializers
from ..models import AllowanceType, DeductionType, Payroll, Employees, PayrollPeriod, ZiGRateToUSD
from django.utils.timezone import now
from decimal import Decimal, ROUND_HALF_UP

class ZiGRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZiGRateToUSD
        fields = ['date', 'rate']

class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source='employee.employeeid', read_only=True)
    
    class Meta:
        model = Payroll
        fields = '__all__'
        read_only_fields = ['net_salary_usd', 'net_salary_zig', 'created_at']
        extra_kwargs = {
            'employee': {'write_only': True}
        }

    def get_employee_name(self, obj):
        return f"{obj.employee.firstname} {obj.employee.surname}"

    def _calculate_net_usd(self, base_salary_usd):
        # You can plug in PAYE, NSSA etc here.
        nssa_rate = Decimal('0.045')  # 4.5% example
        paye_rate = Decimal('0.15')   # 15% example
        deductions = (base_salary_usd * nssa_rate) + (base_salary_usd * paye_rate)
        return (base_salary_usd - deductions).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calculate_net_zig(self, base_salary_zig):
        nssa_rate = Decimal('0.045')
        paye_rate = Decimal('0.15')
        deductions = (base_salary_zig * nssa_rate) + (base_salary_zig * paye_rate)
        return (base_salary_zig - deductions).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_latest_exchange_rate(self):
        rate_entry = ZiGRateToUSD.objects.filter(date__lte=now().date()).order_by('-date').first()
        return rate_entry.rate if rate_entry else Decimal('0')

    def create(self, validated_data):
        base_salary_usd = validated_data.get('base_salary_usd', Decimal('0'))
        base_salary_zig = validated_data.get('base_salary_zig', Decimal('0'))

        net_usd = self._calculate_net_usd(base_salary_usd)
        net_zig = self._calculate_net_zig(base_salary_zig)
        exchange_rate = self._get_latest_exchange_rate()

        print(f"Calculated net_usd: {net_usd}, net_zig: {net_zig}, exchange_rate: {exchange_rate}")

        validated_data['net_salary_usd'] = net_usd
        validated_data['net_salary_zig'] = net_zig
        validated_data['exchange_rate'] = exchange_rate

        return super().create(validated_data)


    def update(self, instance, validated_data):
        base_salary_usd = validated_data.get('base_salary_usd', instance.base_salary_usd)
        base_salary_zig = validated_data.get('base_salary_zig', instance.base_salary_zig)

        instance.net_salary_usd = self._calculate_net_usd(base_salary_usd)
        instance.net_salary_zig = self._calculate_net_zig(base_salary_zig)
        instance.exchange_rate = self._get_latest_exchange_rate()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Ensure calculated fields are always shown correctly"""
        representation = super().to_representation(instance)
        
        # Recalculate if net salaries are missing or incorrect
        if representation['net_salary_usd'] == representation['base_salary_usd']:
            representation['net_salary_usd'] = self._calculate_net_usd(
                Decimal(representation['base_salary_usd'])
            )
        
        if representation['net_salary_zig'] == representation['base_salary_zig']:
            representation['net_salary_zig'] = self._calculate_net_zig(
                Decimal(representation['base_salary_zig'])
            )
            
        return representation

class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = '__all__'

class AllowanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowanceType
        fields = '__all__' # Or specify ['id', 'name', 'description']

class DeductionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeductionType
        fields = '__all__' # Or specify ['id', 'name', 'description']


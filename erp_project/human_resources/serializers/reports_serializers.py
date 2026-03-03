from rest_framework import serializers
from ..hr_models import (
    AllowanceType,
    DeductionType,
    Department,
    EmployeeDeduction,
    Employees,
    Position,
)
from django.db import transaction
from django.contrib.auth import get_user_model
from payroll.payroll_models import Payroll

User = get_user_model()


class EmployeeDeductionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='deduction_type.name', read_only=True)
    deduction_type_id = serializers.IntegerField(source='deduction_type.id', read_only=True)

    class Meta:
        model = EmployeeDeduction
        fields = ['id', 'deduction_type_id', 'name', 'amount', 'currency']

class EmployeeSerializer(serializers.ModelSerializer):
    # 1. READ ONLY (Returns "Human Resources")
    user = serializers.StringRelatedField(read_only=True)
    position = serializers.StringRelatedField(read_only=True)
    department = serializers.StringRelatedField(read_only=True)
    reports_to = serializers.StringRelatedField(read_only=True)

    # 2. WRITE ONLY (Accepts ID "1")
    # Source='department' means it saves to the 'department' column in the DB
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, required=False, allow_null=True
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), source='position', write_only=True, required=True
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True, required=True
    )
    reports_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Employees.objects.all(), source='reports_to', write_only=True, required=False, allow_null=True
    )

    # 3. Custom Deductions List
    deductions_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    
    # CORRECT: Remove source='deductions'
    deductions = EmployeeDeductionSerializer(many=True, read_only=True)

    class Meta:
        model = Employees
        fields = [
            'id', 'employee_id', 'first_name', 'surname', 'email', 'phone', 
            'national_id', 'date_of_birth', 'gender', 'marital_status',
            
            # READ Fields
            'user', 'position', 'department', 'reports_to',
            
            # WRITE Fields (CRITICAL: Must be listed here!)
            'user_id', 'position_id', 'department_id', 'reports_to_id',
            
            'employee_type', 'date_joined', 'contract_from', 'contract_to',
            'leave_days_entitled', 'is_active',
            'usd_salary', 'zig_salary', 'pay_frequency',
            'bank_name', 'bank_account', 'pension_fund', 'nssa_number',
            'zimra_tax_number', 'paye_number', 'pays_aids_levy',
            'emergency_contact_name', 'emergency_contact_number', 'emergency_contact_relationship',
            'deductions_data', 'deductions'
        ]
        read_only_fields = ('employee_id',)

    @transaction.atomic
    def create(self, validated_data):
        # Pop deductions (not part of Employee model)
        
        print("\n--- CREATING EMPLOYEE ---")
        print(f"Data Received: {validated_data}")
        
        deductions = validated_data.pop('deductions_data', [])
        
        print(f"Deductions to process: {len(deductions)}")
        
        # Create Employee
        # Note: validated_data automatically converts 'department_id' -> 'department' object
        # because of source='department' in the field definition.
        employee = Employees.objects.create(**validated_data)
        
        print(f"Employee Created: {employee} (ID: {employee.id})")

        # Process Deductions
        for item in deductions:
            try:
                ded_id = item.get('id')
                if ded_id:
                    deduction_type = DeductionType.objects.get(pk=ded_id)
                    EmployeeDeduction.objects.create(
                        employee=employee,
                        deduction_type=deduction_type,
                        amount=item.get('amount', 0)
                    )
            except DeductionType.DoesNotExist:
                pass

        return employee


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


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializes the Department model.
    """
    class Meta:
        model = Department
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    """
    Serializes the Position model.
    - Reads 'department' as a string name (e.g. "HR").
    - Writes 'department_id' as an ID (e.g. 1).
    """
    # Read: Show name ("HR")
    department = serializers.StringRelatedField(read_only=True)
    
    # Write: Accept ID (1) from the dropdown
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        source='department', 
        write_only=True
    )

    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'department', 'department_id']

# Add this near your other serializers
class DeductionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeductionType
        fields = '__all__' # id, name, description

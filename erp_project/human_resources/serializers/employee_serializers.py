from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from ..hr_models import (
    DeductionType,
    EmployeeDeduction,
    Employees,
    Department,
    Position,  # Import Position model
    TrainingProgram,
    TrainingSession,
    TrainingCertification,
    TrainingEnrollment,
    AttendanceRecord
)

User = get_user_model()

class EmployeeProfileSerializer(serializers.ModelSerializer):
    """
    A simple serializer to nest inside the User object.
    It provides the key HR info needed for the frontend app state.
    """
    # Use StringRelatedField to show "HR" instead of department ID 3
    department = serializers.StringRelatedField()
    position = serializers.StringRelatedField()
    role = serializers.ReadOnlyField(source='role.name')
    role_permissions = serializers.ReadOnlyField(source='role.permissions')

    class Meta:
        model = Employees
        # List all the fields your frontend needs to know about the user
        fields = [
            'employee_id', 
            'role', 
            'department', 
            'position',
            'date_joined',
            'is_active',
            'role_permissions',
        ]

# We need a serializer for Position to use in EmployeeSerializer
class PositionSerializer(serializers.ModelSerializer):
    """
    Serializes the Position model.
    - Reads 'department' as a string.
    - Writes 'department_id' as a primary key.
    """
    department = serializers.StringRelatedField(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        source='department', 
        write_only=True
    )

    class Meta:
        model = Position
        fields = ['id', 'title', 'department', 'department_id', 'description']


class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializes the Department model.
    Includes all fields.
    """
    class Meta:
        model = Department
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializes the Employees model with relationships.
    Handles creating Employees AND their initial deductions.
    """

    # --- Read-only fields (Strings) ---
    user = serializers.StringRelatedField(read_only=True)
    position = serializers.StringRelatedField(read_only=True)
    department = serializers.StringRelatedField(read_only=True)
    reports_to = serializers.StringRelatedField(read_only=True)

    # --- Write-only fields (IDs) ---
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, allow_null=True, required=False
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(), source='position', write_only=True, allow_null=True, required=False
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True, allow_null=True, required=False
    )
    reports_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Employees.objects.all(), source='reports_to', write_only=True, allow_null=True, required=False
    )

    def to_representation(self, instance):
        """Add department_id and position_id to output for frontend dropdowns."""
        data = super().to_representation(instance)
        data['department_id'] = instance.department.id if instance.department else None
        data['position_id'] = instance.position.id if instance.position else None
        return data

    def validate(self, attrs):
        """
        Validate that the position belongs to the selected department.
        """
        department = attrs.get('department')
        position = attrs.get('position')

        # If updating, get current values from instance if not provided
        if self.instance:
            if department is None and 'department' not in attrs:
                department = self.instance.department
            if position is None and 'position' not in attrs:
                position = self.instance.position

        # If both department and position are set, validate they match
        if department and position:
            if position.department != department:
                raise serializers.ValidationError({
                    'position_id': f'Position "{position.title}" does not belong to department "{department.name}". Please select a position from the chosen department.'
                })

        return attrs

    # --- NEW: Deductions List from Frontend ---
    # This accepts: [{ "id": 1, "name": "NSSA" }, ...]
    deductions_data = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Employees
        fields = [
            'id', 'employee_id', 'first_name', 'surname', 'email', 'phone',
            'national_id', 'date_of_birth', 'gender', 'marital_status',
            'user', 'position', 'department', 'reports_to',
            'user_id', 'position_id', 'department_id', 'reports_to_id',
            'employee_type', 'date_joined', 'contract_from', 'contract_to',
            'leave_days_entitled', 'is_active',
            'usd_salary', 'zig_salary', 'pay_frequency',
            'bank_name', 'bank_account', 'pension_fund', 'nssa_number',
            'zimra_tax_number', 'paye_number', 'pays_aids_levy',
            'emergency_contact_name', 'emergency_contact_number', 'emergency_contact_relationship',
            'deductions_data'
        ]
        # employee_id is optional - auto-generated if not provided 

    @transaction.atomic
    def create(self, validated_data):
        """
        Custom create method to handle the Employee AND the Deductions list.
        """
        # 1. Pop the deductions data (it doesn't belong in the Employees table)
        deductions = validated_data.pop('deductions_data', [])
        
        # 2. Create the Employee
        # Note: Because we used source='department' in the fields above, 
        # DRF has already converted 'department_id' -> 'department' object in validated_data.
        employee = Employees.objects.create(**validated_data)

        # 3. Process Deductions
        for item in deductions:
            # The frontend sends { "id": 1, "name": "NSSA" ... }
            # We need to find the DeductionType by ID
            try:
                ded_id = item.get('id')
                if ded_id:
                    deduction_type = DeductionType.objects.get(pk=ded_id)
                    
                    # Create the link. Default amount to 0 if not provided.
                    EmployeeDeduction.objects.create(
                        employee=employee,
                        deduction_type=deduction_type,
                        amount=item.get('amount', 0) 
                    )
            except DeductionType.DoesNotExist:
                print(f"Warning: DeductionType ID {ded_id} not found.")
                continue

        return employee

class TrainingProgramSerializer(serializers.ModelSerializer):
    """
    Serializes the TrainingProgram model.
    """
    class Meta:
        model = TrainingProgram
        fields = '__all__'


# --- NEW: Training Certification Serializer ---
class TrainingCertificationSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employees.objects.all(),
        source='employee',
        write_only=True
    )
    program = serializers.StringRelatedField(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=TrainingProgram.objects.all(),
        source='program',
        write_only=True,
        allow_null=True,
        required=False
    )
    
    # Make 'status' read-only since it's a @property
    status = serializers.CharField(read_only=True)

    class Meta:
        model = TrainingCertification
        fields = [
            'id', 'employee', 'employee_id', 'program', 'program_id', 
            'certification_name', 'issue_date', 'expiry_date', 'status'
        ]

# --- NEW: Attendance Record Serializer ---
class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employees.objects.all(),
        source='employee',
        write_only=True
    )

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_id', 'date', 'time_in', 'time_out'
        ]


class TrainingSessionSerializer(serializers.ModelSerializer):
    """
    Serializes the TrainingSession model with relationships.
    - Reads 'program' as a string.
    - Writes 'program_id' as a primary key.
    """
    # For reading (GET)
    program = serializers.StringRelatedField(read_only=True)
    
    # For writing (POST/PUT)
    program_id = serializers.PrimaryKeyRelatedField(
        queryset=TrainingProgram.objects.all(), 
        source='program', 
        write_only=True
    )

    class Meta:
        model = TrainingSession
        fields = ['id', 'program', 'program_id', 'trainer', 'date', 'venue', 'status']
        


class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employees.objects.all(),
        source='employee',
        write_only=True
    )
    session = TrainingSessionSerializer(read_only=True) # Nested read-only
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=TrainingSession.objects.all(),
        source='session',
        write_only=True
    )
    
    class Meta:
        model = TrainingEnrollment
        fields = [
            'id', 'employee', 'employee_id', 'session', 'session_id', 'status'
        ]
        


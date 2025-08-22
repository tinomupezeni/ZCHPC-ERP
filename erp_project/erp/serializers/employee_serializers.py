from rest_framework import serializers

from ..serializers.payroll_serializer import AllowanceTypeSerializer, DeductionTypeSerializer
from ..models import AllowanceType, CustomUser, DeductionType, Employees
from datetime import datetime

class UserRegistrationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    last_login_at = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['email', 'employeeid', 'firstname', 'isActive', 'surname', 'role', 'department', 'department_name', 'password', 'salary', 'contractFrom', 'contractTo', 'last_login_at']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_last_login_at(self, obj):
        log = obj.auditlog_set.filter(event_type="SUCCESS").order_by("-timestamp").first()
        return log.timestamp if log else None

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def create(self, validated_data):
        validated_data['username'] = validated_data['email']
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            firstname=validated_data.get('firstname', ''),
            surname=validated_data.get('surname', ''),
            role=validated_data.get('role', ''),
            department=validated_data.get('department', ''),
            salary=validated_data.get('salary', None),
            contractFrom=validated_data.get('contractFrom', None),
            contractTo=validated_data.get('contractTo', None),
        )
        return user

class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = [
            'employeeid', 'firstname', 'surname', 'nationalid', 
            'dateOfBirth', 'gender', 'maritalStatus', 'email', 'phone',
            'position', 'department', 'employee_type', 'leave_days',
            'contractFrom', 'contractTo', 'usd_salary', 'zig_salary',
            'frequency', 'bankName', 'bankAccount', 'pensionFund',
            'nssaNumber', 'zimraTaxNumber', 'payeNumber', 'aidsLevyNumber',
            'emegencyContactName', 'emegencyContactNumber', 'emegencyContactRelationship'
        ]
    
    def validate(self, data):
        
        # Convert salary strings to numbers
        if 'usd_salary' in data:
            data['usd_salary'] = float(data['usd_salary'])
        if 'zig_salary' in data:
            data['zig_salary'] = float(data['zig_salary'])
        
        return data

    def create(self, validated_data):
        # Handle empty strings for optional fields
        for field in ['bankName', 'bankAccount', 'pensionFund', 'nssaNumber', 
                     'zimraTaxNumber', 'payeNumber', 'aidsLevyNumber']:
            if field in validated_data and validated_data[field] == "":
                validated_data[field] = None
        
        return Employees.objects.create(**validated_data)
    
# --- Modified: EmployeePayslipSerializer ---
class EmployeePayslipSerializer(serializers.ModelSerializer):
    # Option 1: Nested Read-Only for GET requests (displaying full allowance/deduction objects)
    # This shows the full allowance/deduction object on GET requests including id, name, and amount.
    allowances = AllowanceTypeSerializer(many=True, read_only=True)
    deductions = DeductionTypeSerializer(many=True, read_only=True)

    # Option 2: Write-Only for PUT/PATCH requests (sending only IDs for updates)
    # This field is used when you send data to update the allowances/deductions for an employee.
    # It expects a list of IDs of AllowanceType objects.
    allowance_ids = serializers.PrimaryKeyRelatedField(
        queryset=AllowanceType.objects.all(), # Defines what AllowanceType objects are valid
        many=True, # Indicates it's a list of IDs
        write_only=True, # This field is only used for input, not output
        source='allowances' # It maps directly to the 'allowances' ManyToManyField on the Employee model
    )
    deduction_ids = serializers.PrimaryKeyRelatedField(
        queryset=DeductionType.objects.all(), # Defines what DeductionType objects are valid
        many=True, # Indicates it's a list of IDs
        write_only=True, # This field is only used for input, not output
        source='deductions' # It maps directly to the 'deductions' ManyToManyField on the Employee model
    )

    class Meta:
        model = Employees # Ensure this is your Employee model with ManyToMany fields
        fields = [
            'employeeid', 'firstname', 'isActive', 'surname', 'position', 'department',
            'contractFrom', 'contractTo', 'phone', 'usd_salary', 'zig_salary',
            'allowances', 'deductions', # For GET requests (read-only nested objects)
            'allowance_ids', 'deduction_ids' # For PUT/PATCH requests (write-only IDs)
        ]
        # 'password' is not a field on Employees model, remove it from extra_kwargs
        # extra_kwargs = {'password': {'write_only': True}} # This line is likely an error here

    # You won't typically validate email for an existing employee in a payslip serializer.
    # This validation seems more appropriate for a registration or profile update serializer.
    # If this serializer is used for updating employee details including email, ensure its logic.
    # For now, I'm removing it as it's not typical for a "payslip" view.
    # If Employees.objects.filter(email=value).exists() is meant to check for *other* employees
    # having the same email, it needs to exclude the current instance being updated.
    # def validate_email(self, value):
    #     if Employees.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("This email is already in use.")
    #     return value

    # Override the update method to properly handle ManyToMany fields
    def update(self, instance, validated_data):
        # Extract allowance and deduction IDs from validated_data
        # 'source' maps 'allowance_ids' to 'allowances' in validated_data
        allowances_data = validated_data.pop('allowances', None)
        deductions_data = validated_data.pop('deductions', None)

        # Update the basic fields first
        instance = super().update(instance, validated_data)

        # Then update the ManyToMany relationships
        if allowances_data is not None:
            # .set() replaces all existing relationships with the new set of IDs
            instance.allowances.set(allowances_data)
        if deductions_data is not None:
            # .set() replaces all existing relationships with the new set of IDs
            instance.deductions.set(deductions_data)

        instance.save() # Save the instance after ManyToMany updates
        return instance

    # The create method from EmployeePayslipSerializer seems to duplicate EmployeeRegistrationSerializer's role.
    # A serializer named 'Payslip' usually focuses on displaying data or updating salary-related fields,
    # not creating new employees with full details.
    # If this serializer is also used for creating employees, you'll need to adapt this method
    # to handle the new ManyToMany fields for allowances and deductions.
    # For a Payslip serializer, a 'create' method is often not needed, or is simpler.
    # def create(self, validated_data):
    #     user = Employees.objects.create(
    #         email=validated_data['email'],
    #         firstname=validated_data.get('firstname', ''),
    #         surname=validated_data.get('surname', ''),
    #         position=validated_data.get('position', ''),
    #         department=validated_data.get('department', ''),
    #         phone = validated_data.get('phone', ''),
    #         usd_salary=validated_data.get('usd_salary', None),
    #         zig_salary=validated_data.get('zig_salary', None),
    #         contractFrom=validated_data.get('contractFrom', None),
    #         contractTo=validated_data.get('contractTo', None),
    #     )
    #     return user
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

# Import your HR models
from human_resources.hr_models import Employees, Department
from human_resources.serializers.employee_serializers import EmployeeProfileSerializer

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    # 1. Add fields that accept data from Frontend but aren't on the User model
    role = serializers.CharField(write_only=True, required=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        write_only=True, 
        required=True
    )
    
    # 2. Include the nested profile for reading (GET requests)
    employee_profile = EmployeeProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'is_active', 
            'date_joined', 
            'password',
            # Add the new write-only fields here
            'role',
            'department',
            'employee_profile' 
        ]
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'style': {'input_type': 'password'}},
            # Ensure names are required
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates a CustomUser AND an Employee profile in one transaction.
        """
        # 1. Extract HR data
        role = validated_data.pop('role')
        department = validated_data.pop('department')
        password = validated_data.pop('password', 'erp@1234')

        # 2. Capture the basic info before creating the user
        email = validated_data.get('email')
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')

        # 3. Create the User
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # 4. Create the Employee Record 
        # CRITICAL FIX: You must pass email/names here, otherwise they default to ""
        Employees.objects.create(
            user=user,
            role=role,
            department=department,
            is_active=True,
            email=email,            # <--- ADD THIS
            first_name=first_name,  # <--- ADD THIS
            surname=last_name       # <--- ADD THIS (Map last_name to surname)
        )

        return user
    
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # Extract HR data if present
        role = validated_data.pop('role', None)
        department = validated_data.pop('department', None)
        password = validated_data.pop('password', None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        # Update Employee fields if provided
        if role or department:
            # Get or create in case the profile is missing for some reason
            employee, created = Employees.objects.get_or_create(user=instance)
            if role:
                employee.role = role
            if department:
                employee.department = department
            employee.save()

        return instance
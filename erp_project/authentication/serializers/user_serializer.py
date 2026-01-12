# authentication/serializers/user_serializer.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

from human_resources.hr_models import Employees, Department, Role
from human_resources.serializers.employee_serializers import EmployeeProfileSerializer

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    # Now linking to the Role Model instead of a CharField
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), 
        write_only=True, 
        required=True
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), 
        write_only=True, 
        required=True
    )
    
    # Field to return the generated password to the React frontend
    temp_password = serializers.CharField(read_only=True)
    employee_profile = EmployeeProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_active', 
            'date_joined', 'password', 'role', 'department', 
            'employee_profile', 'temp_password'
        ]
        read_only_fields = ['date_joined', 'temp_password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        role_obj = validated_data.pop('role')
        department_obj = validated_data.pop('department')
        
        # 1. Generate a secure random password for the new user
        generated_password = 'erp@1234'
        
        # 2. Create User
        user = User.objects.create_user(
            email=validated_data['email'],
            password=generated_password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        # 3. Create Employee Profile with ForeignKeys
        Employees.objects.create(
            user=user,
            role=role_obj, # This is now a Role instance
            department=department_obj,
            is_active=True,
            email=user.email,
            first_name=user.first_name,
            surname=user.last_name
        )

        # Attach to instance so it can be serialized in the response
        user.temp_password = generated_password
        return user
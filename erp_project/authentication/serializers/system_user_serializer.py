from rest_framework import serializers
from django.contrib.auth import get_user_model

from human_resources.serializers.employee_serializers import EmployeeProfileSerializer

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializes the CustomUser model and nests the related Employee profile.
    """
    # 2. Add this line.
    # 'employee_profile' is the related_name from your Employee model's 'user' field
    employee_profile = EmployeeProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'is_active', 
            'is_staff', 
            'is_superuser', 
            'date_joined', 
            'password',
            'employee_profile'  # 3. Add this field to the list
        ]
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'required': False,
                'style': {'input_type': 'password'}
            }
        }
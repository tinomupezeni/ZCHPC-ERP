from rest_framework import serializers
from ..models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializes the CustomUser model.
    - 'password' is write-only and not required on updates.
    - 'date_joined' is read-only.
    """
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'is_active', 
            'is_staff', 
            'is_superuser', 
            'date_joined', 
            'password'  # Include password field
        ]
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {
                'write_only': True, # Never send the password hash back
                'required': False,  # Not required for updates (PATCH)
                'style': {'input_type': 'password'} # Hides in browsable API
            }
        }
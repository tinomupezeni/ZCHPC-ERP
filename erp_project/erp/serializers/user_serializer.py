from rest_framework import serializers
from ..models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.
    It handles the serialization of user data and the creation of new users with a default password.
    """
    
    # We want to use the email as the username, so we make username not required
    # in the serializer, and handle it in the validation.
    username = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'employeeid', 'firstname', 'surname', 'role', 
            'department', 'email', 'isActive', 'username'
        ]
        read_only_fields = ['employeeid', 'isActive']
        
        # We need to make the password field write_only for security
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        """
        Custom validation to ensure the username is set to the email if not provided.
        """
        # Set the username from the email if it's not provided
        if not data.get('username') and 'email' in data:
            data['username'] = data['email']
        elif not data.get('username'):
            raise serializers.ValidationError({"username": "This field is required."})
            
        return data

    def create(self, validated_data):
        """
        Create and return a new user with a default password.
        The password is set using set_password() for proper hashing.
        """
        # Pop the password from validated_data to avoid passing it to create() directly
        password = validated_data.pop('password', 'erp@1234')
        
        user = CustomUser.objects.create(**validated_data)
        
        # Set the password using the `set_password` method
        user.set_password(password)
        user.save()
        
        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing user.
        Handle password changes securely using set_password().
        """
        # Handle password update separately
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance
from erp.dependencies import *

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # Exclude password from the fields
        fields = [
            'id', 'employeeid', 'firstname', 'surname', 'role', 
            'department', 'email', 'isActive', 'username'
        ]
        read_only_fields = ['employeeid', 'isActive'] # These fields are handled by the backend
        
    def create(self, validated_data):
        # Create a user with a default password and username
        user = CustomUser.objects.create(
            username=validated_data['email'], # Use email as the username
            firstname=validated_data['firstname'],
            surname=validated_data['surname'],
            role=validated_data['role'],
            department=validated_data['department'],
            email=validated_data['email'],
        )
        
        # Set the default password
        user.set_password('erp@1234')
        user.save()
        
        return user
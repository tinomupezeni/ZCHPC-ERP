
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['first_name'] = user.first_name
        token['email'] = user.email
        # Optional: Add role to the token itself if you want to use it in frontend without profile calls
        if hasattr(user, 'employee_profile') and user.employee_profile.role:
            token['role'] = user.employee_profile.role.name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        profile = getattr(self.user, 'employee_profile', None)
        
        # Get role name and department name as strings
        role_name = None
        if profile and profile.role:
            role_name = profile.role.name  # Use .name to get the string "ADMIN"

        dept_name = None
        if profile and profile.department:
            dept_name = profile.department.name

        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'role': role_name,      # Now a string, which IS serializable
            'department': dept_name # Now a string
        }
        
        return data
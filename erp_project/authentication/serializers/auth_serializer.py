
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
        role_display_name = None
        if profile and profile.role:
            role_name = profile.role.name  # Use .name to get the string "ADMIN"
            role_display_name = profile.role.display_name

        dept_name = None
        if profile and profile.department:
            dept_name = profile.department.name

        # Build employee_profile structure that frontend expects
        employee_profile = None
        if profile:
            employee_profile = {
                'id': profile.id,
                'employee_id': profile.employee_id,
                'role': role_name,  # The role name (e.g., "HUMAN_RESOURCES", "HR")
                'role_display_name': role_display_name,  # Human-readable role name
                'department': dept_name,
                'position': profile.position.title if profile.position else None,
            }

        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
            'role': role_name,  # Keep for backwards compatibility
            'department': dept_name,
            'employee_profile': employee_profile,  # Add nested structure
        }

        return data
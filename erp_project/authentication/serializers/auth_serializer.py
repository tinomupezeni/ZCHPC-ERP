
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        # This method adds custom data (claims) *inside* the token
        token = super().get_token(user)

        # Add custom claims
        token['first_name'] = user.first_name
        token['email'] = user.email

        return token

    def validate(self, attrs):
        # Let the parent class handle authentication
        data = super().validate(attrs)

        profile = getattr(self.user, 'employee_profile', None)
        
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'role': profile.role if profile else None,
            'department': profile.department.name if profile and profile.department else None
        }
        
        return data
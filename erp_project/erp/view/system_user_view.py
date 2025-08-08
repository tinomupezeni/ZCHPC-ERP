from rest_framework import viewsets
from rest_framework import permissions
from ..models import CustomUser
from ..serializers.system_user_serializer import CustomUserSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing CustomUser objects.
    Provides create, retrieve, update, and delete actions.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    # We can customize the get_queryset to exclude the user's password field
    def get_queryset(self):
        # In a real-world app, you might want to restrict this further
        return CustomUser.objects.all().exclude(password='')
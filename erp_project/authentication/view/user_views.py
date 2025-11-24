# users/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model

from ..serializers.user_serializer import CustomUserSerializer

User = get_user_model()

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing User objects.
    Standard CRUD is handled by ModelViewSet logic using the smart Serializer.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Standard users see only themselves.
        Admins/Staff see everyone.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the profile of the currently authenticated user.
        Endpoint: /api/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def unlock(self, request, pk=None):
        """
        Custom action to manually unlock a user account.
        Endpoint: /api/users/{id}/unlock/
        """
        user = self.get_object()
        # This method exists on your CustomUser model
        if hasattr(user, 'reset_failed_attempts'):
            user.reset_failed_attempts()
            return Response({"status": "User account unlocked", "failed_attempts": 0})
        return Response({"error": "Model does not support locking"}, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # NOTE: We removed create(), update(), partial_update(), destroy()
    # The default ModelViewSet methods automatically call 
    # serializer.save(), which now correctly handles password hashing
    # defined in your CustomUserSerializer.
    # ------------------------------------------------------------------
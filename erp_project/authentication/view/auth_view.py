from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView

from ..models import CustomUser, AuditLog
from ..serializers.auth_serializer import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view to add audit logging for login attempts.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        
        if 'email' in data and 'username' not in data:
            data['username'] = data['email']

        username_attempt = data.get("email") or data.get("username")
        
        print(f"DEBUG: Attempting login for: {username_attempt}")
        
        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)

        except (AuthenticationFailed, ValidationError) as e:
            print(f"DEBUG: Login Failed: {e.detail}")
            # Login failed
            user = None
            try:
                # Find the user (if they exist) to log the failed attempt
                if username_attempt:
                    # Try fetching by email 
                    user = CustomUser.objects.get(email=username_attempt)
                    user.register_failed_attempt()
            except CustomUser.DoesNotExist:
                print("DEBUG: User does not exist in DB")
                pass
            
            log_login_event(user, username_attempt, request, "FAILED")
            
            return Response(e.detail, status=e.status_code)

        # If we reach here, login was successful
        user = serializer.user
        
        # Reset failed attempts on success
        if hasattr(user, 'reset_failed_attempts'):
            user.reset_failed_attempts()
        
        log_login_event(user, user.email, request, "SUCCESS")

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


def get_client_ip(request):
    """
    Get the client's real IP address. Respects X-Forwarded-For.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")

def log_login_event(user, username, request, event_type):
    """
    Creates an AuditLog entry for a login event.
    """
    # Fallback if username/email is None
    attempted = username or (user.email if user else "UNKNOWN")

    AuditLog.objects.create(
        user=user, 
        username_attempted=attempted,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        event_type=event_type,
    )
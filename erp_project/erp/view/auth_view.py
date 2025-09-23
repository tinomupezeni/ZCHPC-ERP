
from erp.dependencies import *
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("\n====== LOGIN DEBUG START ======")
        print("RAW request.data:", request.data)

        email = request.data.get("username")  # ⚠️ you are sending 'username', not 'email'
        password = request.data.get("password")
        print("Extracted -> email:", email, "| password:", password)

        serializer = self.get_serializer(data=request.data)
        try:
            is_valid = serializer.is_valid(raise_exception=True)
            print("Serializer is_valid result:", is_valid)
        except Exception as e:
            print("❌ Serializer validation failed:", str(e))
            print("Serializer errors:", serializer.errors)

            # Log failed attempts
            try:
                user = CustomUser.objects.get(email=email)
                print("Found user for failed attempt:", user)
                user.register_failed_attempt()
                log_login_event(user, email, request, "FAILED")
            except CustomUser.DoesNotExist:
                print("User does not exist for email:", email)
                log_login_event(None, email, request, "FAILED")

            print("====== LOGIN DEBUG END (FAILED) ======\n")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Successful login
        user = serializer.user
        print("Serializer returned user:", user)

        user.reset_failed_attempts()
        log_login_event(user, email, request, "SUCCESS")
        print("====== LOGIN DEBUG END (SUCCESS) ======\n")

        return super().post(request, *args, **kwargs)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")

def log_login_event(user, username, request, event_type):
    # fallback if username is None
    attempted = username or (user.email if user else "UNKNOWN")

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        username_attempted=attempted,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        event_type=event_type,
    )


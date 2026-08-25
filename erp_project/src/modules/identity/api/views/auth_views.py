"""
Authentication API views.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView


from modules.identity.api.serializers import (
    AuditLogSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
)
from modules.identity.application.services import AuthService, LoginCommand
from modules.identity.infrastructure.persistence.audit_repository import DjangoAuditLogRepository
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository


class LoginView(APIView):
    """
    API endpoint for user authentication.

    POST /api/v2/auth/token/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Authenticate user and return JWT tokens.

        Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }

        Response:
        {
            "access": "jwt-access-token",
            "refresh": "jwt-refresh-token",
            "user": {
                "id": "uuid",
                "email": "user@example.com",
                ...
            }
        }
        """
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get client info for audit logging
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Create service and authenticate
        auth_service = AuthService(
            user_repository=DjangoUserRepository(),
            audit_repository=DjangoAuditLogRepository(),
        )

        result = auth_service.authenticate(
            LoginCommand(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        if not result.success:
            return Response(
                {"detail": result.error or "Authentication failed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate JWT tokens using SimpleJWT
        from modules.identity.infrastructure.persistence.models import CustomUser

        db_user = CustomUser.objects.get(id=result.user.id)
        refresh = RefreshToken.for_user(db_user)

        # Add custom claims
        refresh["email"] = result.user.email
        refresh["first_name"] = result.user.first_name

        # Get employee profile if exists
        employee_data = None
        if hasattr(db_user, "employee_profile") and db_user.employee_profile:
            emp = db_user.employee_profile
            # Reverse OneToOne raises RelatedObjectDoesNotExist (an AttributeError
            # subclass) when absent, so getattr(..., None) is the safe accessor.
            employment_details = getattr(emp, "employment_details", None)
            employee_data = {
                "id": emp.id,
                "employee_id": emp.employee_id,
                "role": emp.role.name if emp.role else None,
                "role_display_name": emp.role.display_name if emp.role else None,
                "department": (
                    employment_details.department.name
                    if employment_details and employment_details.department else None
                ),
                "position": (
                    employment_details.position.title
                    if employment_details and employment_details.position else None
                ),
            }
            refresh["role"] = emp.role.name if emp.role else None

        response_data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(result.user.id),
                "email": result.user.email,
                "first_name": result.user.first_name,
                "last_name": result.user.last_name,
                "is_staff": result.user.is_staff,
                "is_superuser": result.user.is_superuser,
                "employee_profile": employee_data,
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")


class AuditLogListView(APIView):
    """
    API endpoint for viewing audit logs.

    GET /api/v2/auth/logs/
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        List audit log entries.

        Query params:
        - username: Filter by username attempted
        - ip_address: Filter by IP address
        - event_type: Filter by event type (SUCCESS, FAILED, LOCKOUT)
        - limit: Number of results (default 100)
        - offset: Pagination offset
        """
        username = request.query_params.get("username")
        ip_address = request.query_params.get("ip_address")
        event_type = request.query_params.get("event_type")
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))

        repo = DjangoAuditLogRepository()
        entries = repo.search(
            username=username,
            ip_address=ip_address,
            event_type=event_type,
            limit=limit,
            offset=offset,
        )

        serializer = AuditLogSerializer(
            [e.to_dict() for e in entries],
            many=True,
        )

        return Response({
            "count": repo.count(event_type=event_type),
            "results": serializer.data,
        })

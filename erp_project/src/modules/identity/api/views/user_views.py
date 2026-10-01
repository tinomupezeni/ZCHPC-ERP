"""
User management API views.
"""

from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

from modules.hr.application.authorization import (
    EmployeeAuthorizationPolicy,
    resolve_actor_permissions,
)
from modules.identity.api.serializers import (
    ChangePasswordRequestSerializer,
    CreateUserRequestSerializer,
    CreateUserResponseSerializer,
    UpdateUserRequestSerializer,
    UserResponseSerializer,
)
from modules.identity.application.services import (
    CreateUserCommand,
    UpdateUserCommand,
    UserService,
)
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository


def _error(exc, http_status):
    return Response({"detail": exc.message, "code": exc.code}, status=http_status)


class UserListCreateView(APIView):
    """
    API endpoint for listing and creating users.

    GET /api/v2/auth/users/
    POST /api/v2/auth/users/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List users.

        Admins see all users, regular users see only themselves.
        """
        service = UserService(DjangoUserRepository())

        if request.user.is_staff or request.user.is_superuser:
            include_inactive = request.query_params.get("include_inactive", "false")
            users = service.list_users(
                include_inactive=include_inactive.lower() == "true",
                # Logins of archived employees (AUD-02) only with
                # hr.employee.view_archived.
                include_archived=EmployeeAuthorizationPolicy().may_view_archived(
                    resolve_actor_permissions(request.user)
                ),
            )
        else:
            # Non-admin users can only see themselves
            try:
                users = [service.get_user(request.user.id)]
            except NotFoundError:
                users = []

        serializer = UserResponseSerializer(
            [u.__dict__ for u in users],
            many=True,
        )
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new user.

        Needs hr.employee.create (checked by UserService). Also creates the
        employee record, through EmployeeService, if role/department provided.
        """
        serializer = CreateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            result = service.create_user(
                CreateUserCommand(
                    email=serializer.validated_data["email"],
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    password=serializer.validated_data.get("password"),
                    role_id=serializer.validated_data.get("role"),
                    department_id=serializer.validated_data.get("department"),
                ),
                actor_permissions=resolve_actor_permissions(request.user),
                actor_email=request.user.email,
            )

            # Return flat response structure expected by frontend
            response_data = {
                "id": result.user.id,
                "email": result.user.email,
                "first_name": result.user.first_name,
                "last_name": result.user.last_name,
                # One-time generated password (null when the creator chose
                # one). Either way the owner must replace it at first login.
                "temporary_password": result.temp_password,
                "must_change_password": result.user.must_change_password,
            }

            return Response(
                response_data,
                status=status.HTTP_201_CREATED,
            )

        except AuthorizationError as e:
            return _error(e, status.HTTP_403_FORBIDDEN)
        except ConflictError as e:
            return _error(e, status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return _error(e, status.HTTP_400_BAD_REQUEST)
        except NotFoundError as e:
            # e.g. an unknown department - same mapping as the hr employees API
            return _error(e, status.HTTP_404_NOT_FOUND)


class UserDetailView(APIView):
    """
    API endpoint for user details.

    GET /api/v2/auth/users/{id}/
    PATCH /api/v2/auth/users/{id}/

    There is deliberately no DELETE (AUD-02): an employee's identity and
    history are never destroyed through the application. DELETE gets DRF's
    405 Method Not Allowed and changes nothing; access is ended through the
    lifecycle instead (PATCH is_active=false, or the hr deactivate endpoint).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id: str):
        """Get user details."""
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Non-admins can only view themselves
        if not (request.user.is_staff or request.user.is_superuser):
            if uuid_id != request.user.id:
                return Response(
                    {"detail": "Not authorized"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service = UserService(DjangoUserRepository())

        # The login of an archived employee (AUD-02) exists only for an actor
        # holding hr.employee.view_archived.
        if service.is_archived_account(uuid_id) and not EmployeeAuthorizationPolicy().may_view_archived(
            resolve_actor_permissions(request.user)
        ):
            return Response(
                {"detail": f"User with ID {uuid_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user = service.get_user(uuid_id)
            serializer = UserResponseSerializer(user.__dict__)
            return Response(serializer.data)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, user_id: str):
        """Update user details."""
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            result = service.update_user(
                UpdateUserCommand(
                    user_id=uuid_id,
                    first_name=serializer.validated_data.get("first_name"),
                    last_name=serializer.validated_data.get("last_name"),
                    is_active=serializer.validated_data.get("is_active"),
                ),
                actor_permissions=resolve_actor_permissions(request.user),
                actor_user_id=request.user.id,
            )
            data = dict(UserResponseSerializer(result.user.__dict__).data)
            if result.temp_password is not None:
                # Reactivation issued a new one-time password (REM-07).
                data["temporary_password"] = result.temp_password
            return Response(data)
        except AuthorizationError as e:
            return _error(e, status.HTTP_403_FORBIDDEN)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            # e.g. the account's employee is archived (AUD-02)
            return _error(e, status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """
    API endpoint for current user info.

    GET /api/v2/auth/users/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current authenticated user."""
        service = UserService(DjangoUserRepository())

        try:
            user = service.get_user(request.user.id)
            serializer = UserResponseSerializer(user.__dict__)
            return Response(serializer.data)
        except NotFoundError:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChangePasswordView(APIView):
    """
    Self-service password change.

    POST /api/v2/auth/password/change/

    Always acts on the authenticated caller - no user id is accepted - and
    requires the current password. Reachable while must_change_password is
    set (RBACMiddleware). The stored hash changes, which revokes every
    previously issued token, so fresh tokens are returned.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = UserService(DjangoUserRepository())
        try:
            user = service.change_password(
                request.user.id,
                new_password=serializer.validated_data["new_password"],
                current_password=serializer.validated_data["current_password"],
            )
        except ValidationError as e:
            return Response(
                {"detail": e.message, "code": e.code, **(e.details or {})},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from rest_framework_simplejwt.tokens import RefreshToken

        from modules.identity.infrastructure.persistence.models import CustomUser

        refresh = RefreshToken.for_user(CustomUser.objects.get(pk=user.id))
        return Response(
            {
                "detail": "Password changed.",
                "must_change_password": user.must_change_password,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class UnlockUserView(APIView):
    """
    API endpoint to unlock a user account.

    POST /api/v2/auth/users/{id}/unlock/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id: str):
        """Unlock a user account (needs hr.employee.reactivate, checked by UserService)."""
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            user = service.unlock_user(
                uuid_id,
                actor_permissions=resolve_actor_permissions(request.user),
                actor_user_id=request.user.id,
            )
            serializer = UserResponseSerializer(user.__dict__)
            return Response(serializer.data)
        except AuthorizationError as e:
            return _error(e, status.HTTP_403_FORBIDDEN)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )

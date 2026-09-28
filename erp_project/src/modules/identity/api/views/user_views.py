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

from modules.hr.application.authorization import resolve_actor_permissions
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
            users = service.list_users(include_inactive=include_inactive.lower() == "true")
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
                "password": result.temp_password,
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
    DELETE /api/v2/auth/users/{id}/
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
            user = service.update_user(
                UpdateUserCommand(
                    user_id=uuid_id,
                    first_name=serializer.validated_data.get("first_name"),
                    last_name=serializer.validated_data.get("last_name"),
                    is_active=serializer.validated_data.get("is_active"),
                ),
                actor_permissions=resolve_actor_permissions(request.user),
                actor_user_id=request.user.id,
            )
            response_serializer = UserResponseSerializer(user.__dict__)
            return Response(response_serializer.data)
        except AuthorizationError as e:
            return _error(e, status.HTTP_403_FORBIDDEN)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, user_id: str):
        """Permanently delete a user (needs hr.employee.delete, checked by UserService)."""
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            service.delete_user(
                uuid_id,
                actor_permissions=resolve_actor_permissions(request.user),
                actor_user_id=request.user.id,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AuthorizationError as e:
            return _error(e, status.HTTP_403_FORBIDDEN)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )


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

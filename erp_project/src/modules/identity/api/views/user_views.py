"""
User management API views.
"""

from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError

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

        Admin only. Optionally creates an employee profile if role/department provided.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

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
                    is_staff=serializer.validated_data.get("is_staff", False),
                    is_superuser=serializer.validated_data.get("is_superuser", False),
                )
            )

            # Create employee profile if role or department provided
            role_id = serializer.validated_data.get("role")
            department_id = serializer.validated_data.get("department")

            if role_id or department_id:
                from modules.hr.infrastructure.persistence.models import (
                    Department, Employees, Role
                )
                from modules.identity.infrastructure.persistence.models import CustomUser

                db_user = CustomUser.objects.get(id=result.user.id)

                employee_data = {
                    "user": db_user,
                    "first_name": result.user.first_name,
                    "surname": result.user.last_name,
                    "email": result.user.email,
                    "is_active": True,
                }

                if role_id:
                    try:
                        role = Role.objects.get(id=role_id)
                        employee_data["role"] = role
                    except Role.DoesNotExist:
                        pass

                if department_id:
                    try:
                        department = Department.objects.get(id=department_id)
                        employee_data["department"] = department
                    except Department.DoesNotExist:
                        pass

                Employees.objects.create(**employee_data)

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

        except ConflictError as e:
            return Response(
                {"detail": e.message, "code": e.code},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as e:
            return Response(
                {"detail": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )


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

        # Only admins can update other users
        is_self = uuid_id == request.user.id
        if not is_self and not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UpdateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Non-admins cannot change is_active or is_staff
        if not (request.user.is_staff or request.user.is_superuser):
            if "is_active" in serializer.validated_data or "is_staff" in serializer.validated_data:
                return Response(
                    {"detail": "Cannot modify these fields"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service = UserService(DjangoUserRepository())

        try:
            user = service.update_user(
                UpdateUserCommand(
                    user_id=uuid_id,
                    first_name=serializer.validated_data.get("first_name"),
                    last_name=serializer.validated_data.get("last_name"),
                    is_active=serializer.validated_data.get("is_active"),
                    is_staff=serializer.validated_data.get("is_staff"),
                )
            )
            response_serializer = UserResponseSerializer(user.__dict__)
            return Response(response_serializer.data)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, user_id: str):
        """Delete a user. Admin only."""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            service.delete_user(uuid_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
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

    permission_classes = [IsAdminUser]

    def post(self, request, user_id: str):
        """Unlock a user account."""
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return Response(
                {"detail": "Invalid user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserService(DjangoUserRepository())

        try:
            user = service.unlock_user(uuid_id)
            serializer = UserResponseSerializer(user.__dict__)
            return Response(serializer.data)
        except NotFoundError as e:
            return Response(
                {"detail": e.message},
                status=status.HTTP_404_NOT_FOUND,
            )

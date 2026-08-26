"""
User management application service.

Orchestrates user CRUD operations.
"""

import secrets
import string

from dataclasses import dataclass
from uuid import UUID

from click import command

from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError
from shared.domain.value_objects import Email

from modules.identity.application.interfaces import (
    IUserRepository,
    UserDTO,
)
from modules.identity.domain.entities import User
from modules.identity.domain.value_objects import HashedPassword


@dataclass
class CreateUserCommand:
    """Command to create a new user."""

    email: str
    first_name: str
    last_name: str
    password: str | None = None  # If None, generates temp password
    is_staff: bool = False
    is_superuser: bool = False


@dataclass
class UpdateUserCommand:
    """Command to update a user."""

    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_staff: bool | None = None


@dataclass
class CreateUserResult:
    """Result of user creation."""

    user: UserDTO
    temp_password: str | None = None


def generate_temp_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure random temporary password.

    Uses Python's secrets module for security-sensitive random values.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class UserService:
    """
    Application service for user management.

    Handles CRUD operations and user administration.
    """

    def __init__(self, user_repository: IUserRepository) -> None:
        """
        Initialize user service.

        Args:
            user_repository: Repository for user data
        """
        self._user_repo = user_repository

    def create_user(self, command: CreateUserCommand) -> CreateUserResult:
        """
        Create a new user.

        Args:
            command: User creation command

        Returns:
            CreateUserResult with user and temp password

        Raises:
            ConflictError: If email already exists
            ValidationError: If data is invalid
        """
        # Check for duplicate email
        email = command.email.lower().strip()
        if self._user_repo.exists_by_email(email):
            raise ConflictError(
                f"User with email {email} already exists",
                code="DUPLICATE_EMAIL",
                details={"email": email},
            )

        # generate temp password
        if command.password:
            password = command.password
            temp_password = None
        else:
            password = temp_password = generate_temp_password()
        
        # Create user
        user = User.create(
            email=email,
            password=password,
            first_name=command.first_name,
            last_name=command.last_name,
            is_staff=command.is_staff,
            is_superuser=command.is_superuser,
        )

        self._user_repo.add(user)

        return CreateUserResult(
            user=self._to_dto(user),
            temp_password=temp_password,
        )

    def get_user(self, user_id: UUID) -> UserDTO:
        """
        Get a user by ID.

        Args:
            user_id: User's UUID

        Returns:
            UserDTO

        Raises:
            NotFoundError: If user not found
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )
        return self._to_dto(user)

    def get_user_by_email(self, email: str) -> UserDTO:
        """
        Get a user by email.

        Args:
            email: User's email

        Returns:
            UserDTO

        Raises:
            NotFoundError: If user not found
        """
        user = self._user_repo.get_by_email(email.lower().strip())
        if user is None:
            raise NotFoundError(
                f"User with email {email} not found",
                code="USER_NOT_FOUND",
                details={"email": email},
            )
        return self._to_dto(user)

    def list_users(self, include_inactive: bool = False) -> list[UserDTO]:
        """
        List all users.

        Args:
            include_inactive: Whether to include deactivated users

        Returns:
            List of UserDTOs
        """
        users = self._user_repo.get_all(include_inactive=include_inactive)
        return [self._to_dto(u) for u in users]

    def update_user(self, command: UpdateUserCommand) -> UserDTO:
        """
        Update a user.

        Args:
            command: Update command

        Returns:
            Updated UserDTO

        Raises:
            NotFoundError: If user not found
        """
        user = self._user_repo.get_by_id(command.user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {command.user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(command.user_id)},
            )

        # Apply updates
        if command.first_name is not None:
            user.first_name = command.first_name.strip()

        if command.last_name is not None:
            user.last_name = command.last_name.strip()

        if command.is_active is not None:
            if command.is_active:
                user.activate()
            else:
                user.deactivate()

        if command.is_staff is not None:
            user.is_staff = command.is_staff

        self._user_repo.update(user)

        return self._to_dto(user)

    def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user.

        Args:
            user_id: User's UUID

        Returns:
            True if deleted

        Raises:
            NotFoundError: If user not found
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )

        return self._user_repo.delete(user_id)

    def unlock_user(self, user_id: UUID) -> UserDTO:
        """
        Manually unlock a user account.

        Args:
            user_id: User's UUID

        Returns:
            Updated UserDTO

        Raises:
            NotFoundError: If user not found
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )

        user.unlock()
        self._user_repo.update(user)

        return self._to_dto(user)

    def change_password(
        self,
        user_id: UUID,
        new_password: str,
        current_password: str | None = None,
    ) -> None:
        """
        Change a user's password.

        Args:
            user_id: User's UUID
            new_password: New password
            current_password: Current password (for self-change)

        Raises:
            NotFoundError: If user not found
            ValidationError: If current password is wrong
        """
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )

        # Verify current password if provided
        if current_password is not None:
            if not user.verify_password(current_password):
                raise ValidationError(
                    "Current password is incorrect",
                    code="INVALID_CURRENT_PASSWORD",
                )

        user.change_password(new_password)
        self._user_repo.update(user)

    def _to_dto(self, user: User) -> UserDTO:
        """Convert User entity to DTO."""
        return UserDTO(
            id=user.id,
            email=user.email.value,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_active=user.is_active,
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
        )

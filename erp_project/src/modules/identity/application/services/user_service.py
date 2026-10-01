"""
User management application service.

Orchestrates user CRUD operations.

Authorization (REM-08) lives here, not in the HTTP view, so a caller that
skips the view or the middleware is held to the same rules. Every mutating
method takes the acting user's permissions (resolve_actor_permissions) and
is judged by the same EmployeeAuthorizationPolicy REM-01 introduced - an
application login is an employee's login, so there is one policy for both:

- create: hr.employee.create; any role goes through EmployeeService and so
  through REM-01's assignment rules (manage_assignments, role must exist,
  no role above the actor's own permissions, no self-escalation);
- disable a login: hr.employee.deactivate; re-enable or unlock one:
  hr.employee.reactivate - each refusing the actor's own account and anyone
  holding more than the actor.

There is no delete (AUD-02): a login and the employee record behind it are
never destroyed through the application. Access ends through the employee
lifecycle (update_user is_active=False -> EmployeeLifecycleService).

Staff and superuser status are never written here. They are platform-level
flags granted only by operator bootstrap (createsuperuser, seed_admin,
create_test_account, entrypoint.sh), never by an API caller.

Credentials (REM-07): every login this service creates or re-enables holds a
password someone other than its owner knows - chosen by the creator or
issued by generate_temp_password() - so it is marked must_change_password
and RBACMiddleware confines it to the password change until the owner
replaces it (change_password). Reactivation never restores the previous
password; it issues a new temporary one.
"""

import secrets
import string

from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError
from shared.domain.value_objects import Email

from modules.hr.application.authorization import EmployeeAuthorizationPolicy
from modules.identity.application.interfaces import (
    IUserRepository,
    UserDTO,
)
from modules.identity.domain.entities import User
from modules.identity.domain.value_objects import PermissionSet



@dataclass
class CreateUserCommand:
    """Command to create a new user, optionally with an employee record."""

    email: str
    first_name: str
    last_name: str
    password: str | None = None  # If None, generates temp password
    role_id: int | None = None
    department_id: int | None = None


@dataclass
class UpdateUserCommand:
    """Command to update a user."""

    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None


@dataclass
class CreateUserResult:
    """Result of user creation."""

    user: UserDTO
    temp_password: str | None = None


@dataclass
class UpdateUserResult:
    """Result of a user update; a reactivation issues a temporary password."""

    user: UserDTO
    temp_password: str | None = None


def generate_temp_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure random temporary password.

    Uses Python's secrets module for security-sensitive random values.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def disable_login(user_repository: IUserRepository, user_id: UUID) -> bool:
    """
    Switch a login off. Returns True if it was on.

    SimpleJWT refuses a disabled login on every request and on refresh, so
    this also ends every token already issued to it.
    """
    user = user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        return False
    user.deactivate()
    user_repository.update(user)
    return True


def enable_login(user_repository: IUserRepository, user_id: UUID) -> str | None:
    """
    Switch a disabled login back on (REM-07).

    The previous password is never restored: a new temporary one is issued
    and returned once, and the owner must replace it. Returns None, and
    changes nothing, if the login is missing or already enabled.
    """
    user = user_repository.get_by_id(user_id)
    if user is None or user.is_active:
        return None
    temporary_password = generate_temp_password()
    user.issue_temporary_password(temporary_password)
    user.activate()
    user_repository.update(user)
    return temporary_password


class UserService:
    """
    Application service for user management.

    Handles CRUD operations and user administration.
    """

    def __init__(self, user_repository: IUserRepository, employee_service=None) -> None:
        """
        Initialize user service.

        Args:
            user_repository: Repository for user data
            employee_service: modules.hr EmployeeService used to create the
                employee record for a new login (built on first use if None)
        """
        self._user_repo = user_repository
        self._employee_service = employee_service
        self._policy = EmployeeAuthorizationPolicy()

    def create_user(
        self,
        command: CreateUserCommand,
        actor_permissions: PermissionSet | None = None,
        actor_email: str | None = None,
    ) -> CreateUserResult:
        """
        Create a new login and, if a role or department is given, its
        employee record - both or neither.

        Args:
            command: User creation command
            actor_permissions: The acting user's permissions. None holds
                nothing. Needs hr.employee.create; the employee record is
                created by EmployeeService, which applies REM-01's
                role-assignment rules.
            actor_email: The acting user's login email, from the
                authenticated request (REM-01's self-assignment check).

        Returns:
            CreateUserResult with user and temp password

        Raises:
            AuthorizationError: If the actor may not create this account or
                assign the requested role
            ConflictError: If email already exists
            ValidationError: If data is invalid (including an unknown role)
            NotFoundError: If the requested department does not exist
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_create(actor_permissions)

        # Check for duplicate email
        email = command.email.lower().strip()
        if self._user_repo.exists_by_email(email):
            raise ConflictError(
                f"User with email {email} already exists",
                code="DUPLICATE_EMAIL",
                details={"email": email},
            )

        # Use provided password or generate a secure temporary password
        if command.password:
            password = command.password
            temp_password = None
        else:
            password = generate_temp_password()
            temp_password = password

        # Staff/superuser are deliberately not parameters: a created login
        # never holds platform-level authority. Whoever created it knows its
        # password, so the owner must replace it at first login (REM-07).
        user = User.create(
            email=email,
            password=password,
            first_name=command.first_name,
            last_name=command.last_name,
            must_change_password=True,
        )

        with transaction.atomic():
            self._user_repo.add(user)
            if command.role_id is not None or command.department_id is not None:
                self._create_employee_record(user, command, actor_permissions, actor_email)

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

    def update_user(
        self,
        command: UpdateUserCommand,
        actor_permissions: PermissionSet | None = None,
        actor_user_id: UUID | None = None,
    ) -> UpdateUserResult:
        """
        Update a user.

        Anyone may change their own name. Changing another user's name needs
        hr.employee.create (authority over provisioning logins). Disabling a
        login needs hr.employee.deactivate and re-enabling one needs
        hr.employee.reactivate; both refuse the actor's own account and
        anyone holding permissions the actor lacks.

        Disabling or re-enabling the login of an employee is an employee
        lifecycle transition (AUD-02): the employee record moves with it
        (ACTIVE <-> DEACTIVATED) through EmployeeLifecycleService, so the two
        cannot be left disagreeing. An archived employee is refused.

        Re-enabling a disabled login never restores its previous password: a
        new temporary one is issued, returned once, and must be replaced by
        the owner (REM-07).

        Args:
            command: Update command
            actor_permissions: The acting user's permissions (None holds nothing)
            actor_user_id: The acting user's id, from the authenticated request

        Returns:
            UpdateUserResult with the updated user and, on reactivation, the
            temporary password

        Raises:
            AuthorizationError: If the actor may not make this change
            NotFoundError: If user not found
            ValidationError: If the account's employee is archived
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        is_self = actor_user_id is not None and actor_user_id == command.user_id

        # Capabilities first, so an unauthorized caller learns nothing about
        # which user ids exist.
        if command.is_active is True:
            self._policy.authorize_reactivate(actor_permissions)
        elif command.is_active is False:
            self._policy.authorize_deactivate(actor_permissions)
        renames = command.first_name is not None or command.last_name is not None
        if renames and not is_self:
            self._policy.authorize_create(actor_permissions)

        user = self._get(command.user_id)

        if command.is_active is not None:
            authorize_target = (
                self._policy.authorize_reactivate_target
                if command.is_active
                else self._policy.authorize_deactivate_target
            )
            authorize_target(
                actor_permissions,
                target_permissions=self._account_permissions(user.id),
                is_self=is_self,
            )

        # Enabling or disabling access is an employee lifecycle transition
        # (AUD-02): the login and the employee record change together, in
        # this transaction, or not at all.
        temp_password = None
        with transaction.atomic():
            if command.is_active is not None:
                temp_password = self._set_access(user.id, command.is_active)
                user = self._get(user.id)

            if renames:
                if command.first_name is not None:
                    user.first_name = command.first_name.strip()
                if command.last_name is not None:
                    user.last_name = command.last_name.strip()
                self._user_repo.update(user)

        return UpdateUserResult(user=self._to_dto(user), temp_password=temp_password)

    def _set_access(self, user_id: UUID, active: bool) -> str | None:
        """
        Enable or disable this account through the one transition authority.

        A login that belongs to an employee goes through
        EmployeeLifecycleService, which moves the employee and the login
        together. A login with no employee record (e.g. a bootstrap
        superuser) has no employment lifecycle; only its switch changes.

        Returns the temporary password issued if a login was re-enabled.
        """
        from modules.hr.infrastructure.persistence.models import Employees

        employee_id = (
            Employees.objects.filter(user_id=user_id).values_list("pk", flat=True).first()
        )
        if employee_id is None:
            if active:
                return enable_login(self._user_repo, user_id)
            disable_login(self._user_repo, user_id)
            return None

        lifecycle = self._lifecycle_service()
        if active:
            return lifecycle.reactivate(employee_id).temporary_password
        lifecycle.deactivate(employee_id)
        return None

    def _lifecycle_service(self):
        from modules.hr.application.services import EmployeeLifecycleService
        from modules.hr.infrastructure.persistence.employee_repository import (
            DjangoEmployeeRepository,
        )

        return EmployeeLifecycleService(
            employee_repository=DjangoEmployeeRepository(),
            user_repository=self._user_repo,
        )

    def unlock_user(
        self,
        user_id: UUID,
        actor_permissions: PermissionSet | None = None,
        actor_user_id: UUID | None = None,
    ) -> UserDTO:
        """
        Manually unlock a user account.

        Lifting a lockout re-enables a login, so it is governed like
        reactivation: hr.employee.reactivate, never on the actor's own
        account or on anyone holding permissions the actor lacks.

        Args:
            user_id: User's UUID
            actor_permissions: The acting user's permissions (None holds nothing)
            actor_user_id: The acting user's id, from the authenticated request

        Returns:
            Updated UserDTO

        Raises:
            AuthorizationError: If the actor may not unlock this account
            NotFoundError: If user not found
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_reactivate(actor_permissions)

        user = self._get(user_id)
        self._policy.authorize_reactivate_target(
            actor_permissions,
            target_permissions=self._account_permissions(user.id),
            is_self=actor_user_id is not None and actor_user_id == user.id,
        )

        user.unlock()
        self._user_repo.update(user)

        return self._to_dto(user)

    def change_password(
        self,
        user_id: UUID,
        new_password: str,
        current_password: str,
    ) -> UserDTO:
        """
        Change a user's own password (self-service; REM-07).

        ``user_id`` must be the authenticated caller's own id - the view
        passes request.user.id and nothing else - and the current password
        must be proven. The new password is checked by the configured
        AUTH_PASSWORD_VALIDATORS. Success ends the forced-change state; the
        stored hash changes, so every token issued before it stops working
        (SIMPLE_JWT CHECK_REVOKE_TOKEN).

        Args:
            user_id: The caller's own UUID
            new_password: New password
            current_password: The caller's current password

        Returns:
            The updated UserDTO

        Raises:
            NotFoundError: If user not found
            ValidationError: If the current password is wrong or the new one
                is rejected
        """
        user = self._get(user_id)

        if not current_password or not user.verify_password(current_password):
            raise ValidationError(
                "Current password is incorrect",
                code="INVALID_CURRENT_PASSWORD",
            )
        if new_password == current_password:
            raise ValidationError(
                "The new password must differ from the current one",
                code="PASSWORD_UNCHANGED",
            )
        self._validate_new_password(user, new_password)

        user.change_password(new_password)
        self._user_repo.update(user)
        return self._to_dto(user)

    @staticmethod
    def _validate_new_password(user: User, new_password: str) -> None:
        """Apply the project's AUTH_PASSWORD_VALIDATORS."""
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError

        from modules.identity.infrastructure.persistence.models import CustomUser

        # UserAttributeSimilarityValidator needs the model instance (it reads
        # field verbose names as well as values).
        subject = CustomUser.objects.filter(pk=user.id).first()
        try:
            validate_password(new_password, user=subject)
        except DjangoValidationError as exc:
            raise ValidationError(
                " ".join(exc.messages),
                code="INVALID_NEW_PASSWORD",
                details={"errors": list(exc.messages)},
            ) from None

    def _get(self, user_id: UUID) -> User:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError(
                f"User with ID {user_id} not found",
                code="USER_NOT_FOUND",
                details={"user_id": str(user_id)},
            )
        return user

    def _account_permissions(self, user_id: UUID) -> PermissionSet:
        """
        What the target login can actually do, resolved exactly as for an
        acting user (superuser => full access, else its employee role).
        """
        from modules.hr.application.authorization import resolve_actor_permissions
        from modules.identity.infrastructure.persistence.models import CustomUser

        db_user = CustomUser.objects.filter(pk=user_id).first()
        if db_user is None:
            return PermissionSet.empty()
        return resolve_actor_permissions(db_user)

    def _create_employee_record(
        self,
        user: User,
        command: CreateUserCommand,
        actor_permissions: PermissionSet,
        actor_email: str | None,
    ) -> None:
        """
        Create the new login's employee record through EmployeeService, so
        REM-01's creation and role-assignment rules are the only ones applied.
        """
        from modules.hr.application.services import CreateEmployeeCommand

        if self._employee_service is None:
            from modules.hr.application.services import EmployeeService
            from modules.hr.infrastructure.persistence.department_repository import (
                DjangoDepartmentRepository,
            )
            from modules.hr.infrastructure.persistence.employee_repository import (
                DjangoEmployeeRepository,
            )
            from modules.hr.infrastructure.persistence.position_repository import (
                DjangoPositionRepository,
            )

            self._employee_service = EmployeeService(
                employee_repository=DjangoEmployeeRepository(),
                department_repository=DjangoDepartmentRepository(),
                position_repository=DjangoPositionRepository(),
            )

        self._employee_service.create_employee(
            CreateEmployeeCommand(
                first_name=user.first_name,
                surname=user.last_name,
                email=user.email.value,
                role_id=command.role_id,
                department_id=command.department_id,
                user_id=user.id,
            ),
            actor_permissions=actor_permissions,
            actor_email=actor_email,
        )

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
            must_change_password=user.must_change_password,
        )


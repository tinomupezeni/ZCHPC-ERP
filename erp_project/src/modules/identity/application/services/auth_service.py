"""
Authentication application service.

Orchestrates authentication use cases.
"""

from dataclasses import dataclass
from uuid import UUID

from shared.domain.exceptions import BusinessRuleViolationError, NotFoundError

from modules.identity.application.interfaces import (
    AuthResult,
    IAuditLogRepository,
    IUserRepository,
    UserDTO,
)
from modules.identity.domain.entities import AuditLogEntry, User
from modules.identity.domain.events import LoginFailedEvent, LoginSucceededEvent
from modules.identity.domain.services import default_lockout_policy


@dataclass
class LoginCommand:
    """Command for user login."""

    email: str
    password: str
    ip_address: str
    user_agent: str


class AuthService:
    """
    Application service for authentication operations.

    Orchestrates login, token generation, and audit logging.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        audit_repository: IAuditLogRepository,
    ) -> None:
        """
        Initialize auth service.

        Args:
            user_repository: Repository for user data
            audit_repository: Repository for audit logs
        """
        self._user_repo = user_repository
        self._audit_repo = audit_repository
        self._lockout_policy = default_lockout_policy

    def authenticate(self, command: LoginCommand) -> AuthResult:
        """
        Authenticate a user with email and password.

        Args:
            command: Login command with credentials

        Returns:
            AuthResult with success status and tokens/user info
        """
        # Find user by email
        user = self._user_repo.get_by_email(command.email.lower().strip())

        if user is None:
            self._log_failed_login(
                email=command.email,
                ip_address=command.ip_address,
                user_agent=command.user_agent,
                reason="User not found",
            )
            return AuthResult(
                success=False,
                error="Invalid email or password",
            )

        # Check if account is active
        can_login, error = user.can_login()
        if not can_login:
            self._log_failed_login(
                email=command.email,
                ip_address=command.ip_address,
                user_agent=command.user_agent,
                user_id=user.id,
                reason=error or "Account issue",
            )
            return AuthResult(
                success=False,
                error=error,
            )

        # Verify password
        if not user.verify_password(command.password):
            is_locked = user.register_failed_login()
            self._user_repo.update(user)

            if is_locked:
                self._log_account_locked(
                    user=user,
                    ip_address=command.ip_address,
                    user_agent=command.user_agent,
                )

            self._log_failed_login(
                email=command.email,
                ip_address=command.ip_address,
                user_agent=command.user_agent,
                user_id=user.id,
                reason="Invalid password",
            )

            return AuthResult(
                success=False,
                error="Invalid email or password",
            )

        # Successful login
        user.reset_failed_attempts()
        self._user_repo.update(user)

        self._log_successful_login(
            user=user,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
        )

        # Generate tokens (delegated to infrastructure)
        tokens = self._generate_tokens(user)

        return AuthResult(
            success=True,
            user=self._to_user_dto(user),
            access_token=tokens.get("access"),
            refresh_token=tokens.get("refresh"),
        )

    def _generate_tokens(self, user: User) -> dict[str, str]:
        """
        Generate JWT tokens for user.

        This is a placeholder - actual implementation uses
        Django REST Framework SimpleJWT.
        """
        # In real implementation, this would use SimpleJWT
        # For now, return empty - API layer handles this
        return {}

    def _log_successful_login(
        self,
        user: User,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """Log a successful login."""
        entry = AuditLogEntry.create_login_success(
            user_id=user.id,
            email=user.email.value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._audit_repo.add(entry)

        # Also add domain event
        user.add_domain_event(
            LoginSucceededEvent(
                user_id=user.id,
                email=user.email.value,
                ip_address=ip_address,
            )
        )

    def _log_failed_login(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        user_id: UUID | None = None,
        reason: str = "",
    ) -> None:
        """Log a failed login."""
        entry = AuditLogEntry.create_login_failed(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            reason=reason,
        )
        self._audit_repo.add(entry)

    def _log_account_locked(
        self,
        user: User,
        ip_address: str,
        user_agent: str,
    ) -> None:
        """Log account lockout."""
        if user.lockout_until:
            entry = AuditLogEntry.create_account_locked(
                user_id=user.id,
                email=user.email.value,
                ip_address=ip_address,
                user_agent=user_agent,
                locked_until=user.lockout_until,
            )
            self._audit_repo.add(entry)

    def _to_user_dto(self, user: User) -> UserDTO:
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

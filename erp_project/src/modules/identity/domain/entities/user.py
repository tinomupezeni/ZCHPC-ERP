"""
User aggregate root for identity management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import BusinessRuleViolationError, ValidationError
from shared.domain.value_objects import Email

from modules.identity.domain.value_objects import HashedPassword


@dataclass
class User(AggregateRoot[UUID]):
    """
    User aggregate root representing a system user.

    Handles authentication, account status, and lockout logic.

    Attributes:
        id: Unique UUID identifier
        email: User's email address (used for login)
        password: Hashed password
        first_name: User's first name
        last_name: User's last name
        is_active: Whether the account is active
        is_staff: Whether user has staff privileges
        is_superuser: Whether user has superuser privileges
        failed_attempts: Number of consecutive failed login attempts
        lockout_until: Datetime until which account is locked
        date_joined: When the account was created
    """

    email: Email
    password: HashedPassword
    first_name: str
    last_name: str
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    failed_attempts: int = 0
    lockout_until: datetime | None = None
    date_joined: datetime = field(default_factory=datetime.utcnow)

    # Lockout configuration
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    def __init__(
        self,
        id: UUID,
        email: Email,
        password: HashedPassword,
        first_name: str,
        last_name: str,
        is_active: bool = True,
        is_staff: bool = False,
        is_superuser: bool = False,
        failed_attempts: int = 0,
        lockout_until: datetime | None = None,
        date_joined: datetime | None = None,
    ) -> None:
        """Initialize User aggregate."""
        super().__init__(id)
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.is_active = is_active
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.failed_attempts = failed_attempts
        self.lockout_until = lockout_until
        self.date_joined = date_joined or datetime.utcnow()

    @classmethod
    def create(
        cls,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> "User":
        """
        Factory method to create a new user.

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            is_staff: Whether user has staff privileges
            is_superuser: Whether user has superuser privileges

        Returns:
            New User instance with hashed password
        """
        from modules.identity.domain.events import UserCreatedEvent

        user = cls(
            id=uuid4(),
            email=Email(email),
            password=HashedPassword.from_plain_text(password),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        user.add_domain_event(
            UserCreatedEvent(
                user_id=user.id,
                email=user.email.value,
            )
        )

        return user

    @property
    def full_name(self) -> str:
        """User's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_locked_out(self) -> bool:
        """Check if account is currently locked."""
        if self.lockout_until is None:
            return False
        return datetime.utcnow() < self.lockout_until

    def verify_password(self, plain_password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            plain_password: Plain text password to verify

        Returns:
            True if password matches
        """
        return self.password.verify(plain_password)

    def change_password(self, new_password: str) -> None:
        """
        Change the user's password.

        Args:
            new_password: New plain text password
        """
        self.password = HashedPassword.from_plain_text(new_password)

    def register_failed_login(self) -> bool:
        """
        Register a failed login attempt.

        Returns:
            True if account is now locked
        """
        from modules.identity.domain.events import UserLockedEvent

        self.failed_attempts += 1

        if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            self.lockout_until = datetime.utcnow() + timedelta(
                minutes=self.LOCKOUT_DURATION_MINUTES
            )
            self.add_domain_event(
                UserLockedEvent(
                    user_id=self.id,
                    email=self.email.value,
                    locked_until=self.lockout_until,
                )
            )
            return True

        return False

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts after successful login."""
        self.failed_attempts = 0
        self.lockout_until = None

    def unlock(self) -> None:
        """
        Manually unlock the account.

        Used by admins to unlock before lockout expires.
        """
        from modules.identity.domain.events import UserUnlockedEvent

        if self.is_locked_out:
            self.failed_attempts = 0
            self.lockout_until = None
            self.add_domain_event(
                UserUnlockedEvent(
                    user_id=self.id,
                    email=self.email.value,
                )
            )

    def activate(self) -> None:
        """Activate the user account."""
        if self.is_active:
            return
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the user account."""
        if not self.is_active:
            return
        self.is_active = False

    def update_profile(self, first_name: str | None = None, last_name: str | None = None) -> None:
        """
        Update user profile information.

        Args:
            first_name: New first name (if provided)
            last_name: New last name (if provided)
        """
        if first_name is not None:
            self.first_name = first_name.strip()
        if last_name is not None:
            self.last_name = last_name.strip()

    def can_login(self) -> tuple[bool, str | None]:
        """
        Check if user can log in.

        Returns:
            Tuple of (can_login, error_message)
        """
        if not self.is_active:
            return False, "Account is deactivated"

        if self.is_locked_out:
            return False, f"Account is locked until {self.lockout_until}"

        return True, None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "email": self.email.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_staff": self.is_staff,
            "is_superuser": self.is_superuser,
            "is_locked_out": self.is_locked_out,
            "date_joined": self.date_joined.isoformat(),
        }

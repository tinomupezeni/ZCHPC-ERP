"""
Django repository implementation for User aggregate.
"""

from uuid import UUID

from django.db import transaction

from shared.domain.value_objects import Email

from modules.identity.application.interfaces import IUserRepository
from modules.identity.domain.entities import User
from modules.identity.domain.value_objects import HashedPassword


class DjangoUserRepository(IUserRepository):
    """
    Django ORM implementation of IUserRepository.

    Maps between User domain entity and Django's CustomUser model.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of CustomUser model to avoid circular imports."""
        if self._model is None:
            from modules.identity.infrastructure.persistence.models import CustomUser
            self._model = CustomUser
        return self._model

    def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by UUID."""
        try:
            db_user = self.model.objects.get(id=user_id)
            return self._to_entity(db_user)
        except self.model.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        try:
            db_user = self.model.objects.get(email__iexact=email)
            return self._to_entity(db_user)
        except self.model.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> list[User]:
        """Get all users, optionally including inactive."""
        queryset = self.model.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(u) for u in queryset]

    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        return self.model.objects.filter(email__iexact=email).exists()

    @transaction.atomic
    def add(self, user: User) -> None:
        """Add a new user."""
        db_user = self.model(
            id=user.id,
            email=user.email.value,
            password=user.password.value,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
            failed_attempts=user.failed_attempts,
            lockout_until=user.lockout_until,
            date_joined=user.date_joined,
        )
        db_user.save()

    @transaction.atomic
    def update(self, user: User) -> None:
        """Update an existing user."""
        self.model.objects.filter(id=user.id).update(
            email=user.email.value,
            password=user.password.value,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_staff=user.is_staff,
            is_superuser=user.is_superuser,
            failed_attempts=user.failed_attempts,
            lockout_until=user.lockout_until,
        )

    @transaction.atomic
    def delete(self, user_id: UUID) -> bool:
        """Delete a user by ID. Returns True if deleted."""
        deleted, _ = self.model.objects.filter(id=user_id).delete()
        return deleted > 0

    def _to_entity(self, db_user) -> User:
        """Convert Django model to domain entity."""
        return User(
            id=db_user.id,
            email=Email(db_user.email),
            password=HashedPassword.from_hash(db_user.password),
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            is_active=db_user.is_active,
            is_staff=db_user.is_staff,
            is_superuser=db_user.is_superuser,
            failed_attempts=db_user.failed_attempts,
            lockout_until=db_user.lockout_until,
            date_joined=db_user.date_joined,
        )

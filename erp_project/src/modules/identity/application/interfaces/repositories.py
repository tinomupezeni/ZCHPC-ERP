"""
Repository interfaces for the Identity module.

These define the contracts that infrastructure must implement.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from uuid import UUID

from modules.identity.domain.entities import AuditLogEntry, Role, SystemModule, User


class IUserRepository(ABC):
    """
    Repository interface for User aggregate.

    Infrastructure layer must implement this interface
    to provide data persistence for users.
    """

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by UUID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        pass

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> list[User]:
        """Get all users, optionally including inactive."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists."""
        pass

    @abstractmethod
    def add(self, user: User) -> None:
        """Add a new user."""
        pass

    @abstractmethod
    def update(self, user: User) -> None:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Delete a user by ID. Returns True if deleted."""
        pass


class IRoleRepository(ABC):
    """
    Repository interface for Role aggregate.
    """

    @abstractmethod
    def get_by_id(self, role_id: int) -> Role | None:
        """Get role by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        pass

    @abstractmethod
    def get_all(self) -> list[Role]:
        """Get all roles."""
        pass

    @abstractmethod
    def add(self, role: Role) -> None:
        """Add a new role."""
        pass

    @abstractmethod
    def update(self, role: Role) -> None:
        """Update an existing role."""
        pass


class ISystemModuleRepository(ABC):
    """
    Repository interface for SystemModule aggregate.
    """

    @abstractmethod
    def get_by_id(self, module_id: int) -> SystemModule | None:
        """Get module by ID."""
        pass

    @abstractmethod
    def get_by_identifier(self, identifier: str) -> SystemModule | None:
        """Get module by unique identifier (code name)."""
        pass

    @abstractmethod
    def get_all(self, include_inactive: bool = True) -> list[SystemModule]:
        """Get all modules."""
        pass

    @abstractmethod
    def get_active(self) -> list[SystemModule]:
        """Get only active modules."""
        pass

    @abstractmethod
    def add(self, module: SystemModule) -> None:
        """Add a new module."""
        pass

    @abstractmethod
    def update(self, module: SystemModule) -> None:
        """Update an existing module."""
        pass


class IAuditLogRepository(ABC):
    """
    Repository interface for AuditLogEntry.

    Note: Audit logs are append-only. No update or delete methods.
    """

    @abstractmethod
    def add(self, entry: AuditLogEntry) -> AuditLogEntry:
        """
        Add a new audit log entry.

        Returns the entry with ID populated.
        """
        pass

    @abstractmethod
    def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """Get audit entries for a specific user."""
        pass

    @abstractmethod
    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
    ) -> list[AuditLogEntry]:
        """Get all audit entries with optional filtering."""
        pass

    @abstractmethod
    def search(
        self,
        username: str | None = None,
        ip_address: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """Search audit entries by various criteria."""
        pass

    @abstractmethod
    def count(self, event_type: str | None = None) -> int:
        """Count audit entries, optionally filtered by event type."""
        pass

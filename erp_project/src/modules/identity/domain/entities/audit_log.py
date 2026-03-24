"""
Audit log entity for security tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from shared.domain.base import Entity
from shared.domain.exceptions import InvalidOperationError


class AuditEventType(str, Enum):
    """Types of audit events."""

    LOGIN_SUCCESS = "SUCCESS"
    LOGIN_FAILED = "FAILED"
    ACCOUNT_LOCKED = "LOCKOUT"
    PASSWORD_RESET = "FORCE_RESET"
    LOGOUT = "LOGOUT"

    def __str__(self) -> str:
        return self.value


@dataclass
class AuditLogEntry(Entity[int]):
    """
    Audit log entry for tracking security events.

    Audit logs are immutable - they cannot be modified or deleted
    after creation. This ensures a reliable audit trail.

    Attributes:
        id: Unique identifier
        user_id: Reference to the user (if authenticated)
        username_attempted: Email/username used in the attempt
        ip_address: Client IP address
        user_agent: Browser/client user agent string
        event_type: Type of event (SUCCESS, FAILED, LOCKOUT, etc.)
        timestamp: When the event occurred
        details: Additional event details
    """

    user_id: UUID | None
    username_attempted: str
    ip_address: str
    user_agent: str
    event_type: AuditEventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)

    # Flag to prevent modification after creation
    _is_persisted: bool = field(default=False, repr=False)

    def __init__(
        self,
        id: int,
        user_id: UUID | None,
        username_attempted: str,
        ip_address: str,
        user_agent: str,
        event_type: AuditEventType,
        timestamp: datetime | None = None,
        details: dict[str, Any] | None = None,
        _is_persisted: bool = False,
    ) -> None:
        """Initialize AuditLogEntry."""
        super().__init__(id)
        self.user_id = user_id
        self.username_attempted = username_attempted
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.event_type = event_type
        self.timestamp = timestamp or datetime.utcnow()
        self.details = details or {}
        self._is_persisted = _is_persisted

    @classmethod
    def create_login_success(
        cls,
        user_id: UUID,
        email: str,
        ip_address: str,
        user_agent: str,
    ) -> "AuditLogEntry":
        """Create an audit entry for successful login."""
        return cls(
            id=0,  # Will be set by repository
            user_id=user_id,
            username_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type=AuditEventType.LOGIN_SUCCESS,
        )

    @classmethod
    def create_login_failed(
        cls,
        email: str,
        ip_address: str,
        user_agent: str,
        user_id: UUID | None = None,
        reason: str = "",
    ) -> "AuditLogEntry":
        """Create an audit entry for failed login."""
        return cls(
            id=0,
            user_id=user_id,
            username_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type=AuditEventType.LOGIN_FAILED,
            details={"reason": reason} if reason else {},
        )

    @classmethod
    def create_account_locked(
        cls,
        user_id: UUID,
        email: str,
        ip_address: str,
        user_agent: str,
        locked_until: datetime,
    ) -> "AuditLogEntry":
        """Create an audit entry for account lockout."""
        return cls(
            id=0,
            user_id=user_id,
            username_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type=AuditEventType.ACCOUNT_LOCKED,
            details={"locked_until": locked_until.isoformat()},
        )

    @classmethod
    def create_password_reset(
        cls,
        user_id: UUID,
        email: str,
        ip_address: str,
        user_agent: str,
        reset_by: str = "self",
    ) -> "AuditLogEntry":
        """Create an audit entry for password reset."""
        return cls(
            id=0,
            user_id=user_id,
            username_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            event_type=AuditEventType.PASSWORD_RESET,
            details={"reset_by": reset_by},
        )

    def mark_persisted(self) -> None:
        """Mark this entry as persisted (called by repository)."""
        self._is_persisted = True

    def _check_immutable(self) -> None:
        """Raise error if trying to modify persisted entry."""
        if self._is_persisted:
            raise InvalidOperationError(
                "Audit log entries cannot be modified after creation",
                code="AUDIT_LOG_IMMUTABLE",
            )

    @property
    def is_success(self) -> bool:
        """Check if this was a successful event."""
        return self.event_type == AuditEventType.LOGIN_SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if this was a failed event."""
        return self.event_type in (
            AuditEventType.LOGIN_FAILED,
            AuditEventType.ACCOUNT_LOCKED,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "username_attempted": self.username_attempted,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "event_type": str(self.event_type),
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }

"""
Lockout policy domain service.

Encapsulates account lockout business rules.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class LockoutPolicy:
    """
    Domain service that encapsulates account lockout rules.

    Attributes:
        max_failed_attempts: Number of failures before lockout
        lockout_duration_minutes: How long the lockout lasts
    """

    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15

    def should_lock_account(self, failed_attempts: int) -> bool:
        """
        Determine if an account should be locked.

        Args:
            failed_attempts: Current number of failed attempts

        Returns:
            True if account should be locked
        """
        return failed_attempts >= self.max_failed_attempts

    def calculate_lockout_until(self, from_time: datetime | None = None) -> datetime:
        """
        Calculate when the lockout should expire.

        Args:
            from_time: Starting time (defaults to now)

        Returns:
            Datetime when lockout expires
        """
        start = from_time or datetime.utcnow()
        return start + timedelta(minutes=self.lockout_duration_minutes)

    def is_locked_out(self, lockout_until: datetime | None) -> bool:
        """
        Check if an account is currently locked.

        Args:
            lockout_until: The lockout expiration time

        Returns:
            True if still locked out
        """
        if lockout_until is None:
            return False
        return datetime.utcnow() < lockout_until

    def remaining_lockout_seconds(self, lockout_until: datetime | None) -> int:
        """
        Get remaining lockout time in seconds.

        Args:
            lockout_until: The lockout expiration time

        Returns:
            Seconds remaining, or 0 if not locked
        """
        if not self.is_locked_out(lockout_until):
            return 0
        if lockout_until is None:
            return 0
        delta = lockout_until - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


# Default lockout policy instance
default_lockout_policy = LockoutPolicy()

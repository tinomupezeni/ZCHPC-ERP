"""
LeaveType aggregate root.
"""

from datetime import datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


class LeaveType(AggregateRoot[int]):
    """
    LeaveType aggregate root.

    Represents a type of leave (e.g., Annual, Sick, Maternity).
    """

    def __init__(
        self,
        id: int,
        name: str,
        default_days_allowed: int = 0,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize leave type."""
        super().__init__(id)
        self.name = name
        self.default_days_allowed = default_days_allowed
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate leave type data."""
        if not self.name:
            raise ValidationError(
                message="Leave type name is required",
                code="EMPTY_NAME",
            )
        if len(self.name) > 100:
            raise ValidationError(
                message="Leave type name cannot exceed 100 characters",
                code="NAME_TOO_LONG",
            )
        if self.default_days_allowed < 0:
            raise ValidationError(
                message="Default days allowed cannot be negative",
                code="NEGATIVE_DAYS",
            )

    @classmethod
    def create(
        cls,
        id: int,
        name: str,
        default_days_allowed: int = 0,
    ) -> "LeaveType":
        """
        Create a new leave type.

        Args:
            id: Leave type ID
            name: Leave type name
            default_days_allowed: Default number of days allowed

        Returns:
            New LeaveType instance
        """
        return cls(
            id=id,
            name=name.strip(),
            default_days_allowed=default_days_allowed,
            is_active=True,
        )

    def update(
        self,
        name: str | None = None,
        default_days_allowed: int | None = None,
    ) -> None:
        """
        Update leave type details.

        Args:
            name: New name (optional)
            default_days_allowed: New default days (optional)
        """
        if name is not None:
            self.name = name.strip()
        if default_days_allowed is not None:
            self.default_days_allowed = default_days_allowed

        self._validate()
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the leave type."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the leave type."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Debug representation."""
        return f"LeaveType(id={self.id}, name='{self.name}', days={self.default_days_allowed})"

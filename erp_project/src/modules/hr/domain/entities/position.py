"""
Position aggregate root.
"""

from datetime import datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


class Position(AggregateRoot[int]):
    """
    Position aggregate root.

    Represents a job title/position within a department.

    Attributes:
        id: Unique identifier
        title: Position title (unique)
        department_id: ID of the department this position belongs to
        description: Optional description of the position
        created_at: When the position was created
        updated_at: When the position was last updated
    """

    def __init__(
        self,
        id: int,
        title: str,
        department_id: int,
        description: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize position."""
        super().__init__(id)
        self.title = title
        self.department_id = department_id
        self.description = description
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate position data."""
        if not self.title:
            raise ValidationError(
                message="Position title is required",
                code="EMPTY_TITLE",
            )
        if len(self.title) > 100:
            raise ValidationError(
                message="Position title cannot exceed 100 characters",
                code="TITLE_TOO_LONG",
            )
        if not self.department_id:
            raise ValidationError(
                message="Department is required for a position",
                code="MISSING_DEPARTMENT",
            )

    @classmethod
    def create(
        cls,
        id: int,
        title: str,
        department_id: int,
        description: str = "",
    ) -> "Position":
        """
        Create a new position.

        Args:
            id: Position ID
            title: Position title
            department_id: Department ID
            description: Optional description

        Returns:
            New Position instance
        """
        return cls(
            id=id,
            title=title.strip(),
            department_id=department_id,
            description=description.strip() if description else "",
        )

    def update(
        self,
        title: str | None = None,
        department_id: int | None = None,
        description: str | None = None,
    ) -> None:
        """
        Update position details.

        Args:
            title: New title (optional)
            department_id: New department (optional)
            description: New description (optional)
        """
        if title is not None:
            self.title = title.strip()
        if department_id is not None:
            self.department_id = department_id
        if description is not None:
            self.description = description.strip()

        self._validate()
        self.updated_at = datetime.utcnow()

    def move_to_department(self, new_department_id: int) -> None:
        """
        Move position to a different department.

        Args:
            new_department_id: The new department ID
        """
        if not new_department_id:
            raise ValidationError(
                message="New department is required",
                code="MISSING_DEPARTMENT",
            )
        self.department_id = new_department_id
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return self.title

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Position(id={self.id}, title='{self.title}', department_id={self.department_id})"

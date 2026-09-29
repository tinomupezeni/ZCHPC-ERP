"""
Department aggregate root.
"""

from datetime import datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


class Department(AggregateRoot[int]):
    """
    Department aggregate root.

    Represents an organizational unit within the company.

    Attributes:
        id: Unique identifier
        name: Department name (unique)
        description: Optional description of the department
        head_id: Employee accountable for this department (e.g. approves its
            requisitions), or None when the department is between heads.
            Mirrors the existing hr.Department.head foreign key - the
            employee record itself is not duplicated here.
        created_at: When the department was created
        updated_at: When the department was last updated
    """

    def __init__(
        self,
        id: int,
        name: str,
        description: str = "",
        head_id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize department."""
        super().__init__(id)
        self.name = name
        self.description = description
        self.head_id = head_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate department data."""
        if not self.name:
            raise ValidationError(
                message="Department name is required",
                code="EMPTY_NAME",
            )
        if len(self.name) > 100:
            raise ValidationError(
                message="Department name cannot exceed 100 characters",
                code="NAME_TOO_LONG",
            )

    @classmethod
    def create(
        cls,
        id: int,
        name: str,
        description: str = "",
    ) -> "Department":
        """
        Create a new department.

        Args:
            id: Department ID
            name: Department name
            description: Optional description

        Returns:
            New Department instance
        """
        return cls(
            id=id,
            name=name.strip(),
            description=description.strip() if description else "",
        )

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        head_id: int | None = None,
    ) -> None:
        """
        Update department details.

        Args:
            name: New name (optional)
            description: New description (optional)
            head_id: New department head's employee id (optional). Like
                `name`, `None` means "leave unchanged" here, not "clear the
                head" - there is currently no way to unset a recorded head
                through this method, only to reassign it to a different
                employee.
        """
        if name is not None:
            self.name = name.strip()
        if description is not None:
            self.description = description.strip()
        if head_id is not None:
            self.head_id = head_id

        self._validate()
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return self.name

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Department(id={self.id}, name='{self.name}')"

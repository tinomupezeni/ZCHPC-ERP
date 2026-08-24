"""
System Module entity for managing installable ERP modules.
"""

from dataclasses import dataclass, field
from typing import Any

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


@dataclass
class SystemModule(AggregateRoot[int]):
    """
    SystemModule aggregate root representing an installable ERP module.

    Attributes:
        id: Unique identifier
        identifier: Unique code name of the module (e.g., "hr", "payroll")
        name: Human-readable name of the module
        description: Brief description of what the module does
        is_active: Whether the module is currently installed/enabled
        dependencies: List of module identifiers this module depends on
    """

    identifier: str
    name: str
    description: str
    is_active: bool
    dependencies: list[str] = field(default_factory=list)

    def __init__(
        self,
        id: int,
        identifier: str,
        name: str,
        description: str = "",
        is_active: bool = False,
        dependencies: list[str] | None = None,
    ) -> None:
        """Initialize SystemModule aggregate."""
        super().__init__(id)
        self._validate_identifier(identifier)
        self.identifier = identifier.lower().strip()
        self.name = name.strip()
        self.description = description.strip()
        self.is_active = is_active
        self.dependencies = dependencies or []

    @classmethod
    def create(
        cls,
        id: int,
        identifier: str,
        name: str,
        description: str = "",
        is_active: bool = False,
        dependencies: list[str] | None = None,
    ) -> "SystemModule":
        """Factory method to create a new SystemModule."""
        return cls(
            id=id,
            identifier=identifier,
            name=name,
            description=description,
            is_active=is_active,
            dependencies=dependencies,
        )

    @staticmethod
    def _validate_identifier(identifier: str) -> None:
        """Validate module identifier format."""
        if not identifier:
            raise ValidationError(
                "Module identifier cannot be empty",
                code="EMPTY_MODULE_IDENTIFIER",
            )
        if not identifier.replace("_", "").isalnum():
            raise ValidationError(
                "Module identifier must contain only alphanumeric characters and underscores",
                code="INVALID_MODULE_IDENTIFIER",
                details={"identifier": identifier},
            )

    def activate(self) -> None:
        """Activate the module."""
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate the module."""
        self.is_active = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "dependencies": self.dependencies,
        }

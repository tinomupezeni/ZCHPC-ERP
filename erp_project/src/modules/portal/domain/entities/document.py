"""
Document entity for employee portal.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Set

from shared.domain.base import AggregateRoot, Entity
from modules.portal.domain.value_objects import DocumentVisibility


@dataclass
class DocumentAcknowledgement(Entity[int]):
    """Acknowledgement of a document by an employee."""

    document_id: Optional[int]
    employee_id: int
    acknowledged_at: datetime
    ip_address: Optional[str] = None

    @classmethod
    def create(
        cls,
        employee_id: int,
        ip_address: Optional[str] = None,
    ) -> "DocumentAcknowledgement":
        """Create a new acknowledgement."""
        return cls(
            id=None,
            document_id=None,
            employee_id=employee_id,
            acknowledged_at=datetime.now(),
            ip_address=ip_address,
        )


@dataclass
class Document(AggregateRoot[int]):
    """
    Document shared with employees.

    Supports visibility controls and acknowledgement tracking.
    """

    category_id: int
    title: str
    description: str
    file_path: str
    file_type: str
    file_size: int
    visibility: DocumentVisibility
    uploaded_by: int
    version: str = "1.0"
    is_latest: bool = True
    parent_document_id: Optional[int] = None
    is_active: bool = True
    requires_acknowledgement: bool = False
    download_count: int = 0
    department_ids: Set[int] = field(default_factory=set)
    allowed_employee_ids: Set[int] = field(default_factory=set)
    acknowledgements: List[DocumentAcknowledgement] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        category_id: int,
        title: str,
        description: str,
        file_path: str,
        file_type: str,
        file_size: int,
        uploaded_by: int,
        visibility: DocumentVisibility = DocumentVisibility.ALL,
        requires_acknowledgement: bool = False,
    ) -> "Document":
        """Create a new document."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if file_size <= 0:
            raise ValueError("File size must be positive")

        return cls(
            id=None,
            category_id=category_id,
            title=title.strip(),
            description=description or "",
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            visibility=visibility,
            uploaded_by=uploaded_by,
            requires_acknowledgement=requires_acknowledgement,
            acknowledgements=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def can_access(
        self,
        employee_id: int,
        employee_department_id: Optional[int] = None,
    ) -> bool:
        """Check if an employee can access this document."""
        if not self.is_active:
            return False

        if self.visibility == DocumentVisibility.ALL:
            return True

        if self.visibility == DocumentVisibility.DEPARTMENT:
            return (
                employee_department_id is not None
                and employee_department_id in self.department_ids
            )

        if self.visibility == DocumentVisibility.SPECIFIC:
            return employee_id in self.allowed_employee_ids

        return False

    def add_department(self, department_id: int) -> None:
        """Add a department to allowed departments."""
        self.department_ids.add(department_id)
        self.updated_at = datetime.now()

    def remove_department(self, department_id: int) -> None:
        """Remove a department from allowed departments."""
        self.department_ids.discard(department_id)
        self.updated_at = datetime.now()

    def add_allowed_employee(self, employee_id: int) -> None:
        """Add an employee to allowed employees."""
        self.allowed_employee_ids.add(employee_id)
        self.updated_at = datetime.now()

    def remove_allowed_employee(self, employee_id: int) -> None:
        """Remove an employee from allowed employees."""
        self.allowed_employee_ids.discard(employee_id)
        self.updated_at = datetime.now()

    def acknowledge(
        self,
        employee_id: int,
        ip_address: Optional[str] = None,
    ) -> DocumentAcknowledgement:
        """Record an employee's acknowledgement of the document."""
        if not self.requires_acknowledgement:
            raise ValueError("Document does not require acknowledgement")

        # Check if already acknowledged
        for ack in self.acknowledgements:
            if ack.employee_id == employee_id:
                raise ValueError("Document already acknowledged by this employee")

        acknowledgement = DocumentAcknowledgement.create(
            employee_id=employee_id,
            ip_address=ip_address,
        )
        acknowledgement.document_id = self.id
        self.acknowledgements.append(acknowledgement)
        self.updated_at = datetime.now()
        return acknowledgement

    def has_acknowledged(self, employee_id: int) -> bool:
        """Check if an employee has acknowledged this document."""
        return any(ack.employee_id == employee_id for ack in self.acknowledgements)

    def increment_download_count(self) -> None:
        """Increment the download counter."""
        self.download_count += 1

    def deactivate(self) -> None:
        """Deactivate the document."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate the document."""
        self.is_active = True
        self.updated_at = datetime.now()

    @property
    def acknowledgement_count(self) -> int:
        return len(self.acknowledgements)


@dataclass
class DocumentCategory(Entity[int]):
    """Category for organizing documents."""

    name: str
    description: str
    icon: Optional[str] = None
    order: int = 0
    is_active: bool = True

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        icon: Optional[str] = None,
        order: int = 0,
    ) -> "DocumentCategory":
        """Create a new document category."""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        return cls(
            id=None,
            name=name.strip(),
            description=description,
            icon=icon,
            order=order,
            is_active=True,
        )

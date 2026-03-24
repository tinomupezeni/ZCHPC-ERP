"""
Job aggregate root.
"""

from datetime import date, datetime
from typing import Optional, Sequence

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.recruitment.domain.value_objects import JobStatus, SalaryRange


class Job(AggregateRoot[int]):
    """
    Job posting aggregate root.

    Represents a job opening that candidates can apply to.
    """

    def __init__(
        self,
        id: int,
        title: str,
        department_id: int,
        position_id: Optional[int] = None,
        status: JobStatus = JobStatus.DRAFT,
        location: str = "Harare",
        reports_to: str = "ZCHPC Director",
        salary_range: Optional[SalaryRange] = None,
        is_internal: bool = False,
        description: str = "",
        responsibilities: Optional[Sequence[str]] = None,
        qualifications: Optional[Sequence[str]] = None,
        competencies: Optional[Sequence[str]] = None,
        application_process: str = "",
        contact_email: str = "hroffice@zchpc.ac.zw",
        notes: str = "",
        posted_date: Optional[date] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id)
        self.title = title
        self.department_id = department_id
        self.position_id = position_id
        self.status = status
        self.location = location
        self.reports_to = reports_to
        self.salary_range = salary_range or SalaryRange.empty()
        self.is_internal = is_internal
        self.description = description
        self.responsibilities = list(responsibilities) if responsibilities else []
        self.qualifications = list(qualifications) if qualifications else []
        self.competencies = list(competencies) if competencies else []
        self.application_process = application_process
        self.contact_email = contact_email
        self.notes = notes
        self.posted_date = posted_date or date.today()
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self._validate()

    def _validate(self) -> None:
        """Validate job state."""
        if not self.title or not self.title.strip():
            raise ValidationError("Job title is required")
        if self.department_id is None or self.department_id <= 0:
            raise ValidationError("Valid department is required")
        if self.contact_email and "@" not in self.contact_email:
            raise ValidationError("Invalid contact email")

    @property
    def is_open(self) -> bool:
        """Check if job is open for applications."""
        return self.status == JobStatus.OPEN

    @property
    def is_public(self) -> bool:
        """Check if job is visible to public (external candidates)."""
        return not self.is_internal and self.status == JobStatus.OPEN

    def publish(self) -> None:
        """Publish the job (change status to Open)."""
        if self.status == JobStatus.CLOSED:
            raise ValidationError("Cannot publish a closed job. Create a new posting.")
        self.status = JobStatus.OPEN
        self.posted_date = date.today()
        self.updated_at = datetime.now()

    def close(self) -> None:
        """Close the job posting."""
        if self.status == JobStatus.CLOSED:
            raise ValidationError("Job is already closed")
        self.status = JobStatus.CLOSED
        self.updated_at = datetime.now()

    def reopen(self) -> None:
        """Reopen a closed job."""
        if self.status != JobStatus.CLOSED:
            raise ValidationError("Only closed jobs can be reopened")
        self.status = JobStatus.OPEN
        self.posted_date = date.today()
        self.updated_at = datetime.now()

    def update_details(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        responsibilities: Optional[Sequence[str]] = None,
        qualifications: Optional[Sequence[str]] = None,
        competencies: Optional[Sequence[str]] = None,
        application_process: Optional[str] = None,
        location: Optional[str] = None,
        reports_to: Optional[str] = None,
        contact_email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update job details."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if responsibilities is not None:
            self.responsibilities = list(responsibilities)
        if qualifications is not None:
            self.qualifications = list(qualifications)
        if competencies is not None:
            self.competencies = list(competencies)
        if application_process is not None:
            self.application_process = application_process
        if location is not None:
            self.location = location
        if reports_to is not None:
            self.reports_to = reports_to
        if contact_email is not None:
            self.contact_email = contact_email
        if notes is not None:
            self.notes = notes
        self.updated_at = datetime.now()
        self._validate()

    def update_salary_range(self, salary_range: SalaryRange) -> None:
        """Update salary range."""
        self.salary_range = salary_range
        self.updated_at = datetime.now()

    def set_internal_only(self, internal: bool) -> None:
        """Set whether job is internal only."""
        self.is_internal = internal
        self.updated_at = datetime.now()

    def update_department(self, department_id: int) -> None:
        """Update department."""
        if department_id <= 0:
            raise ValidationError("Valid department is required")
        self.department_id = department_id
        self.updated_at = datetime.now()

    def update_position(self, position_id: Optional[int]) -> None:
        """Update position."""
        self.position_id = position_id
        self.updated_at = datetime.now()

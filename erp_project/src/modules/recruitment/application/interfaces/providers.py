"""
Recruitment provider interfaces.

Interfaces exposed to other modules.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, Sequence


@dataclass(frozen=True)
class JobDTO:
    """Data transfer object for jobs."""

    id: int
    title: str
    department_id: int
    department_name: str
    position_id: int | None
    position_title: str | None
    status: str
    location: str
    reports_to: str
    salary_usd_min: Decimal | None
    salary_usd_max: Decimal | None
    salary_zig_min: Decimal | None
    salary_zig_max: Decimal | None
    is_internal: bool
    description: str
    responsibilities: list[str]
    qualifications: list[str]
    competencies: list[str]
    application_process: str
    contact_email: str
    posted_date: date
    applicants_count: int


@dataclass(frozen=True)
class CandidateDTO:
    """Data transfer object for candidates."""

    id: int
    first_name: str
    last_name: str
    email: str
    national_id: str | None
    phone: str
    address: str
    date_of_birth: date | None
    has_resume: bool
    qualifications: str
    experience: str


@dataclass(frozen=True)
class ApplicationDTO:
    """Data transfer object for applications."""

    id: int
    job_id: int
    job_title: str
    candidate_id: int
    candidate_name: str
    candidate_email: str
    cover_letter: str
    status: str
    applied_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ApplicationStatusDTO:
    """Data transfer object for application status check."""

    job_id: int
    job_title: str
    status: str
    applied_at: datetime


class IRecruitmentProvider(Protocol):
    """
    Interface for recruitment data exposed to other modules.

    Used by HR module for converting candidates to employees.
    """

    def get_job(self, job_id: int) -> JobDTO | None:
        """Get job by ID."""
        ...

    def get_open_jobs(self) -> Sequence[JobDTO]:
        """Get all open jobs."""
        ...

    def get_candidate(self, candidate_id: int) -> CandidateDTO | None:
        """Get candidate by ID."""
        ...

    def get_candidate_by_national_id(self, national_id: str) -> CandidateDTO | None:
        """Get candidate by national ID."""
        ...

    def get_application(self, application_id: int) -> ApplicationDTO | None:
        """Get application by ID."""
        ...

    def get_candidate_applications(
        self,
        candidate_id: int,
    ) -> Sequence[ApplicationStatusDTO]:
        """Get all applications for a candidate."""
        ...

    def has_applied(self, candidate_id: int, job_id: int) -> bool:
        """Check if candidate has applied to a job."""
        ...

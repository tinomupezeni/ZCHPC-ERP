"""
Recruitment repository interfaces.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from modules.recruitment.domain.entities import Application, Candidate, Job
from modules.recruitment.domain.value_objects import ApplicationStatus, JobStatus


class IJobRepository(ABC):
    """Interface for job repository."""

    @abstractmethod
    def get_by_id(self, job_id: int) -> Job | None:
        """Get job by ID."""
        ...

    @abstractmethod
    def get_all(
        self,
        status: JobStatus | None = None,
        department_id: int | None = None,
        is_internal: bool | None = None,
    ) -> Sequence[Job]:
        """Get all jobs with optional filters."""
        ...

    @abstractmethod
    def get_open_jobs(self, is_internal: bool | None = None) -> Sequence[Job]:
        """Get all open jobs."""
        ...

    @abstractmethod
    def get_public_jobs(self) -> Sequence[Job]:
        """Get all public (non-internal, open) jobs."""
        ...

    @abstractmethod
    def save(self, job: Job) -> Job:
        """Save job."""
        ...

    @abstractmethod
    def delete(self, job_id: int) -> None:
        """Delete job."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        status: JobStatus | None = None,
    ) -> Sequence[Job]:
        """Search jobs by title or description."""
        ...


class ICandidateRepository(ABC):
    """Interface for candidate repository."""

    @abstractmethod
    def get_by_id(self, candidate_id: int) -> Candidate | None:
        """Get candidate by ID."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Candidate | None:
        """Get candidate by email."""
        ...

    @abstractmethod
    def get_by_national_id(self, national_id: str) -> Candidate | None:
        """Get candidate by national ID."""
        ...

    @abstractmethod
    def get_all(self) -> Sequence[Candidate]:
        """Get all candidates."""
        ...

    @abstractmethod
    def save(self, candidate: Candidate) -> Candidate:
        """Save candidate."""
        ...

    @abstractmethod
    def delete(self, candidate_id: int) -> None:
        """Delete candidate."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...


class IApplicationRepository(ABC):
    """Interface for application repository."""

    @abstractmethod
    def get_by_id(self, application_id: int) -> Application | None:
        """Get application by ID."""
        ...

    @abstractmethod
    def get_by_job(
        self,
        job_id: int,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get applications for a job."""
        ...

    @abstractmethod
    def get_by_candidate(
        self,
        candidate_id: int,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get applications by candidate."""
        ...

    @abstractmethod
    def get_by_job_and_candidate(
        self,
        job_id: int,
        candidate_id: int,
    ) -> Application | None:
        """Get application by job and candidate."""
        ...

    @abstractmethod
    def get_all(
        self,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get all applications."""
        ...

    @abstractmethod
    def save(self, application: Application) -> Application:
        """Save application."""
        ...

    @abstractmethod
    def delete(self, application_id: int) -> None:
        """Delete application."""
        ...

    @abstractmethod
    def get_next_id(self) -> int:
        """Get next available ID."""
        ...

    @abstractmethod
    def count_by_job(
        self,
        job_id: int,
        status: ApplicationStatus | None = None,
    ) -> int:
        """Count applications for a job."""
        ...

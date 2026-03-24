"""
Job application service.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.recruitment.application.interfaces import IApplicationRepository, IJobRepository, JobDTO
from modules.recruitment.domain.entities import Job
from modules.recruitment.domain.events import JobClosed, JobPosted, JobReopened
from modules.recruitment.domain.value_objects import JobStatus, SalaryRange


@dataclass
class CreateJobCommand:
    """Command to create a job."""

    title: str
    department_id: int
    position_id: int | None = None
    description: str = ""
    responsibilities: list[str] | None = None
    qualifications: list[str] | None = None
    competencies: list[str] | None = None
    location: str = "Harare"
    reports_to: str = "ZCHPC Director"
    salary_usd_min: Decimal | None = None
    salary_usd_max: Decimal | None = None
    salary_zig_min: Decimal | None = None
    salary_zig_max: Decimal | None = None
    is_internal: bool = False
    application_process: str = ""
    contact_email: str = "hroffice@zchpc.ac.zw"
    notes: str = ""
    status: str = "Draft"


@dataclass
class UpdateJobCommand:
    """Command to update a job."""

    job_id: int
    title: str | None = None
    description: str | None = None
    responsibilities: list[str] | None = None
    qualifications: list[str] | None = None
    competencies: list[str] | None = None
    location: str | None = None
    reports_to: str | None = None
    salary_usd_min: Decimal | None = None
    salary_usd_max: Decimal | None = None
    salary_zig_min: Decimal | None = None
    salary_zig_max: Decimal | None = None
    is_internal: bool | None = None
    application_process: str | None = None
    contact_email: str | None = None
    notes: str | None = None


class JobService:
    """
    Application service for job operations.
    """

    def __init__(
        self,
        job_repository: IJobRepository,
        application_repository: IApplicationRepository,
    ) -> None:
        self._job_repo = job_repository
        self._app_repo = application_repository

    def create_job(self, command: CreateJobCommand) -> JobDTO:
        """Create a new job posting."""
        salary_range = SalaryRange(
            usd_min=command.salary_usd_min,
            usd_max=command.salary_usd_max,
            zig_min=command.salary_zig_min,
            zig_max=command.salary_zig_max,
        )

        status = JobStatus.from_string(command.status)

        job = Job(
            id=self._job_repo.get_next_id(),
            title=command.title,
            department_id=command.department_id,
            position_id=command.position_id,
            status=status,
            location=command.location,
            reports_to=command.reports_to,
            salary_range=salary_range,
            is_internal=command.is_internal,
            description=command.description,
            responsibilities=command.responsibilities,
            qualifications=command.qualifications,
            competencies=command.competencies,
            application_process=command.application_process,
            contact_email=command.contact_email,
            notes=command.notes,
        )

        if status == JobStatus.OPEN:
            job.add_event(
                JobPosted(
                    job_id=job.id,
                    title=job.title,
                    department_id=job.department_id,
                    is_internal=job.is_internal,
                    posted_at=datetime.now(),
                )
            )

        saved = self._job_repo.save(job)
        return self._to_dto(saved)

    def update_job(self, command: UpdateJobCommand) -> JobDTO:
        """Update an existing job."""
        job = self._job_repo.get_by_id(command.job_id)
        if not job:
            raise NotFoundError(f"Job with ID {command.job_id} not found")

        job.update_details(
            title=command.title,
            description=command.description,
            responsibilities=command.responsibilities,
            qualifications=command.qualifications,
            competencies=command.competencies,
            location=command.location,
            reports_to=command.reports_to,
            contact_email=command.contact_email,
            notes=command.notes,
            application_process=command.application_process,
        )

        if command.is_internal is not None:
            job.set_internal_only(command.is_internal)

        # Update salary range if any salary field is provided
        if any([
            command.salary_usd_min is not None,
            command.salary_usd_max is not None,
            command.salary_zig_min is not None,
            command.salary_zig_max is not None,
        ]):
            job.update_salary_range(
                SalaryRange(
                    usd_min=command.salary_usd_min or job.salary_range.usd_min,
                    usd_max=command.salary_usd_max or job.salary_range.usd_max,
                    zig_min=command.salary_zig_min or job.salary_range.zig_min,
                    zig_max=command.salary_zig_max or job.salary_range.zig_max,
                )
            )

        saved = self._job_repo.save(job)
        return self._to_dto(saved)

    def publish_job(self, job_id: int) -> JobDTO:
        """Publish a job (change status to Open)."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")

        job.publish()
        job.add_event(
            JobPosted(
                job_id=job.id,
                title=job.title,
                department_id=job.department_id,
                is_internal=job.is_internal,
                posted_at=datetime.now(),
            )
        )

        saved = self._job_repo.save(job)
        return self._to_dto(saved)

    def close_job(self, job_id: int) -> JobDTO:
        """Close a job posting."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")

        job.close()
        job.add_event(
            JobClosed(
                job_id=job.id,
                title=job.title,
                closed_at=datetime.now(),
            )
        )

        saved = self._job_repo.save(job)
        return self._to_dto(saved)

    def reopen_job(self, job_id: int) -> JobDTO:
        """Reopen a closed job."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")

        job.reopen()
        job.add_event(
            JobReopened(
                job_id=job.id,
                title=job.title,
                reopened_at=datetime.now(),
            )
        )

        saved = self._job_repo.save(job)
        return self._to_dto(saved)

    def get_job(self, job_id: int) -> JobDTO:
        """Get a job by ID."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")
        return self._to_dto(job)

    def get_all_jobs(
        self,
        status: str | None = None,
        department_id: int | None = None,
        is_internal: bool | None = None,
    ) -> Sequence[JobDTO]:
        """Get all jobs with optional filters."""
        job_status = JobStatus.from_string(status) if status else None
        jobs = self._job_repo.get_all(
            status=job_status,
            department_id=department_id,
            is_internal=is_internal,
        )
        return [self._to_dto(j) for j in jobs]

    def get_open_jobs(self, is_internal: bool | None = None) -> Sequence[JobDTO]:
        """Get all open jobs."""
        jobs = self._job_repo.get_open_jobs(is_internal=is_internal)
        return [self._to_dto(j) for j in jobs]

    def get_public_jobs(self) -> Sequence[JobDTO]:
        """Get all public (non-internal, open) jobs."""
        jobs = self._job_repo.get_public_jobs()
        return [self._to_dto(j) for j in jobs]

    def search_jobs(
        self,
        query: str,
        status: str | None = None,
    ) -> Sequence[JobDTO]:
        """Search jobs by title or description."""
        job_status = JobStatus.from_string(status) if status else None
        jobs = self._job_repo.search(query=query, status=job_status)
        return [self._to_dto(j) for j in jobs]

    def delete_job(self, job_id: int) -> None:
        """Delete a job."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found")

        # Check for applications
        app_count = self._app_repo.count_by_job(job_id)
        if app_count > 0:
            raise ValidationError(
                f"Cannot delete job with {app_count} applications. "
                "Close the job instead."
            )

        self._job_repo.delete(job_id)

    def _to_dto(self, job: Job) -> JobDTO:
        """Convert entity to DTO."""
        applicants_count = self._app_repo.count_by_job(job.id)

        return JobDTO(
            id=job.id,
            title=job.title,
            department_id=job.department_id,
            department_name="",  # Will be populated by infrastructure
            position_id=job.position_id,
            position_title=None,  # Will be populated by infrastructure
            status=job.status.value,
            location=job.location,
            reports_to=job.reports_to,
            salary_usd_min=job.salary_range.usd_min,
            salary_usd_max=job.salary_range.usd_max,
            salary_zig_min=job.salary_range.zig_min,
            salary_zig_max=job.salary_range.zig_max,
            is_internal=job.is_internal,
            description=job.description,
            responsibilities=list(job.responsibilities),
            qualifications=list(job.qualifications),
            competencies=list(job.competencies),
            application_process=job.application_process,
            contact_email=job.contact_email,
            posted_date=job.posted_date,
            applicants_count=applicants_count,
        )

"""
Recruitment provider implementation.

Provides recruitment data to other modules.
"""

from typing import Sequence

from modules.recruitment.application.interfaces import (
    ApplicationStatusDTO,
    CandidateDTO,
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
    IRecruitmentProvider,
    JobDTO,
    ApplicationDTO,
)


class RecruitmentProvider(IRecruitmentProvider):
    """
    Implementation of IRecruitmentProvider.

    Used by HR module for hiring candidates.
    """

    def __init__(
        self,
        job_repository: IJobRepository,
        candidate_repository: ICandidateRepository,
        application_repository: IApplicationRepository,
    ) -> None:
        self._job_repo = job_repository
        self._candidate_repo = candidate_repository
        self._app_repo = application_repository

    def get_job(self, job_id: int) -> JobDTO | None:
        """Get job by ID."""
        job = self._job_repo.get_by_id(job_id)
        if not job:
            return None

        applicants_count = self._app_repo.count_by_job(job_id)

        return JobDTO(
            id=job.id,
            title=job.title,
            department_id=job.department_id,
            department_name="",  # Not available without HR provider
            position_id=job.position_id,
            position_title=None,
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

    def get_open_jobs(self) -> Sequence[JobDTO]:
        """Get all open jobs."""
        jobs = self._job_repo.get_open_jobs()
        return [self._job_to_dto(j) for j in jobs]

    def get_candidate(self, candidate_id: int) -> CandidateDTO | None:
        """Get candidate by ID."""
        candidate = self._candidate_repo.get_by_id(candidate_id)
        if not candidate:
            return None
        return self._candidate_to_dto(candidate)

    def get_candidate_by_national_id(self, national_id: str) -> CandidateDTO | None:
        """Get candidate by national ID."""
        candidate = self._candidate_repo.get_by_national_id(national_id)
        if not candidate:
            return None
        return self._candidate_to_dto(candidate)

    def get_application(self, application_id: int) -> ApplicationDTO | None:
        """Get application by ID."""
        application = self._app_repo.get_by_id(application_id)
        if not application:
            return None

        job = self._job_repo.get_by_id(application.job_id)
        candidate = self._candidate_repo.get_by_id(application.candidate_id)

        return ApplicationDTO(
            id=application.id,
            job_id=application.job_id,
            job_title=job.title if job else "",
            candidate_id=application.candidate_id,
            candidate_name=candidate.full_name if candidate else "",
            candidate_email=candidate.email if candidate else "",
            cover_letter=application.cover_letter,
            status=application.status.value,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
        )

    def get_candidate_applications(
        self,
        candidate_id: int,
    ) -> Sequence[ApplicationStatusDTO]:
        """Get all applications for a candidate."""
        applications = self._app_repo.get_by_candidate(candidate_id)

        results = []
        for app in applications:
            job = self._job_repo.get_by_id(app.job_id)
            results.append(
                ApplicationStatusDTO(
                    job_id=app.job_id,
                    job_title=job.title if job else "",
                    status=app.status.value,
                    applied_at=app.applied_at,
                )
            )

        return results

    def has_applied(self, candidate_id: int, job_id: int) -> bool:
        """Check if candidate has applied to a job."""
        existing = self._app_repo.get_by_job_and_candidate(
            job_id=job_id,
            candidate_id=candidate_id,
        )
        return existing is not None

    def _job_to_dto(self, job) -> JobDTO:
        """Convert job entity to DTO."""
        applicants_count = self._app_repo.count_by_job(job.id)

        return JobDTO(
            id=job.id,
            title=job.title,
            department_id=job.department_id,
            department_name="",
            position_id=job.position_id,
            position_title=None,
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

    def _candidate_to_dto(self, candidate) -> CandidateDTO:
        """Convert candidate entity to DTO."""
        return CandidateDTO(
            id=candidate.id,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            email=candidate.email,
            national_id=candidate.national_id,
            phone=candidate.phone,
            address=candidate.address,
            date_of_birth=candidate.date_of_birth,
            has_resume=candidate.has_resume,
            qualifications=candidate.qualifications,
            experience=candidate.experience,
        )

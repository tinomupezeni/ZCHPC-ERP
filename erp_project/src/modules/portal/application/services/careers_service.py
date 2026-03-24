"""
Public careers service for job applications.
"""

from dataclasses import dataclass
from typing import List, Optional

from modules.portal.application.interfaces import (
    IRecruitmentProvider,
    JobDTO,
)


@dataclass
class ApplicationResult:
    """Result of job application."""

    success: bool
    application_id: Optional[int] = None
    message: Optional[str] = None


class CareersService:
    """
    Public careers service for job seekers.

    Provides access to job listings and application submission.
    No authentication required.
    """

    def __init__(
        self,
        recruitment_provider: IRecruitmentProvider,
    ) -> None:
        self._recruitment_provider = recruitment_provider

    def get_open_jobs(self) -> List[JobDTO]:
        """
        Get all open job postings.

        Returns:
            List of open jobs
        """
        return self._recruitment_provider.get_open_jobs()

    def get_job(
        self,
        job_id: int,
    ) -> Optional[JobDTO]:
        """
        Get a specific job posting.

        Args:
            job_id: Job ID

        Returns:
            Job details if found and open
        """
        job = self._recruitment_provider.get_job(job_id)

        if job is None:
            return None

        # Only return if open
        if job.status != "Open":
            return None

        return job

    def apply_for_job(
        self,
        job_id: int,
        candidate_data: dict,
    ) -> ApplicationResult:
        """
        Submit a job application.

        Args:
            job_id: Job ID to apply for
            candidate_data: Candidate information including:
                - national_id: National ID number
                - first_name: First name
                - last_name: Last name
                - email: Email address
                - phone: Phone number
                - date_of_birth: Date of birth
                - qualifications: Qualifications/education
                - experience: Work experience
                - cover_letter: Cover letter (optional)
                - resume_path: Path to uploaded resume (optional)

        Returns:
            ApplicationResult with application ID if successful
        """
        # Validate required fields
        required_fields = [
            "national_id", "first_name", "last_name",
            "email", "phone", "date_of_birth",
        ]

        for field in required_fields:
            if not candidate_data.get(field):
                return ApplicationResult(
                    success=False,
                    message=f"Missing required field: {field}"
                )

        # Verify job exists and is open
        job = self.get_job(job_id)
        if job is None:
            return ApplicationResult(
                success=False,
                message="Job not found or not accepting applications"
            )

        try:
            application_id = self._recruitment_provider.apply_for_job(
                job_id=job_id,
                candidate_data=candidate_data,
            )
            return ApplicationResult(
                success=True,
                application_id=application_id,
                message="Application submitted successfully"
            )
        except Exception as e:
            error_msg = str(e)
            if "already applied" in error_msg.lower():
                return ApplicationResult(
                    success=False,
                    message="You have already applied for this position"
                )
            return ApplicationResult(
                success=False,
                message=error_msg
            )

    def check_application_status(
        self,
        national_id: str,
    ) -> List[dict]:
        """
        Check application status by national ID.

        Args:
            national_id: Candidate's national ID

        Returns:
            List of applications with their statuses
        """
        if not national_id:
            return []

        return self._recruitment_provider.check_application_status(
            national_id=national_id.strip(),
        )

    def check_if_applied(
        self,
        job_id: int,
        national_id: str,
    ) -> bool:
        """
        Check if a candidate has already applied for a job.

        Args:
            job_id: Job ID
            national_id: Candidate's national ID

        Returns:
            True if already applied
        """
        applications = self.check_application_status(national_id)

        for app in applications:
            if app.get("job_id") == job_id:
                return True

        return False

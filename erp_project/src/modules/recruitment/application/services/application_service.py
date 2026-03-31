"""
Application service for job applications.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.recruitment.application.interfaces import (
    ApplicationDTO,
    ApplicationStatusDTO,
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
)
from modules.recruitment.domain.entities import Application, Candidate
from modules.recruitment.domain.events import (
    ApplicationReceived,
    ApplicationStatusChanged,
    CandidateCreated,
    CandidateHired,
    CandidateRejected,
    CandidateShortlisted,
)
from modules.recruitment.domain.services import ApplicationProcessor
from modules.recruitment.domain.value_objects import ApplicationStatus


@dataclass
class SubmitApplicationCommand:
    """Command to submit a job application."""

    job_id: int
    # Candidate info - can be new or existing
    national_id: str | None = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    date_of_birth: str | None = None
    qualifications: str = ""
    experience: str = ""
    cover_letter: str = ""
    resume_path: str | None = None


@dataclass
class UpdateApplicationStatusCommand:
    """Command to update application status."""

    application_id: int
    new_status: str


class ApplicationService:
    """
    Application service for job application operations.
    """

    def __init__(
        self,
        application_repository: IApplicationRepository,
        candidate_repository: ICandidateRepository,
        job_repository: IJobRepository,
    ) -> None:
        self._app_repo = application_repository
        self._candidate_repo = candidate_repository
        self._job_repo = job_repository
        self._processor = ApplicationProcessor()

    def submit_application(
        self, command: SubmitApplicationCommand
    ) -> ApplicationDTO:
        """Submit a new job application."""
        # Verify job exists and is open
        job = self._job_repo.get_by_id(command.job_id)
        if not job:
            raise NotFoundError(f"Job with ID {command.job_id} not found")
        if not job.is_open:
            raise ValidationError("Cannot apply to a closed job")

        # Find or create candidate
        candidate = None
        if command.national_id:
            candidate = self._candidate_repo.get_by_national_id(command.national_id)
        if not candidate and command.email:
            candidate = self._candidate_repo.get_by_email(command.email)

        if candidate:
            # Update existing candidate
            candidate.update_contact(
                email=command.email or None,
                phone=command.phone or None,
                address=command.address or None,
            )
            if command.qualifications or command.experience:
                candidate.update_qualifications(
                    qualifications=command.qualifications or None,
                    experience=command.experience or None,
                )
            if command.resume_path:
                candidate.set_resume(command.resume_path)
            candidate = self._candidate_repo.save(candidate)
        else:
            # Create new candidate
            from datetime import date as date_type

            dob = None
            if command.date_of_birth:
                try:
                    dob = date_type.fromisoformat(command.date_of_birth)
                except ValueError:
                    pass

            candidate = Candidate(
                id=self._candidate_repo.get_next_id(),
                first_name=command.first_name,
                last_name=command.last_name,
                email=command.email,
                national_id=command.national_id,
                phone=command.phone,
                address=command.address,
                date_of_birth=dob,
                qualifications=command.qualifications,
                experience=command.experience,
                resume_path=command.resume_path,
            )
            candidate.add_domain_event(
                CandidateCreated(
                    candidate_id=candidate.id,
                    email=candidate.email,
                    national_id=candidate.national_id,
                    created_at=datetime.now(),
                )
            )
            candidate = self._candidate_repo.save(candidate)

        # Check for duplicate application
        existing = self._app_repo.get_by_job_and_candidate(
            job_id=command.job_id,
            candidate_id=candidate.id,
        )
        if existing:
            raise ValidationError("You have already applied to this job")

        # Create application
        application = Application(
            id=self._app_repo.get_next_id(),
            job_id=command.job_id,
            candidate_id=candidate.id,
            cover_letter=command.cover_letter,
        )
        application.add_domain_event(
            ApplicationReceived(
                application_id=application.id,
                job_id=application.job_id,
                candidate_id=application.candidate_id,
                applied_at=datetime.now(),
            )
        )

        saved = self._app_repo.save(application)
        return self._to_dto(saved, job.title, candidate)

    def update_status(
        self, command: UpdateApplicationStatusCommand
    ) -> ApplicationDTO:
        """Update application status."""
        application = self._app_repo.get_by_id(command.application_id)
        if not application:
            raise NotFoundError(
                f"Application with ID {command.application_id} not found"
            )

        new_status = ApplicationStatus.from_string(command.new_status)
        old_status = application.status

        # Validate transition
        can_transition, reason = self._processor.can_transition(
            application, new_status
        )
        if not can_transition:
            raise ValidationError(reason)

        # Process transition
        self._processor.process_transition(application, new_status)

        # Add appropriate event
        application.add_domain_event(
            ApplicationStatusChanged(
                application_id=application.id,
                job_id=application.job_id,
                candidate_id=application.candidate_id,
                old_status=old_status.value,
                new_status=new_status.value,
                changed_at=datetime.now(),
            )
        )

        if new_status == ApplicationStatus.SHORTLISTED:
            application.add_domain_event(
                CandidateShortlisted(
                    application_id=application.id,
                    job_id=application.job_id,
                    candidate_id=application.candidate_id,
                    shortlisted_at=datetime.now(),
                )
            )
        elif new_status == ApplicationStatus.HIRED:
            application.add_domain_event(
                CandidateHired(
                    application_id=application.id,
                    job_id=application.job_id,
                    candidate_id=application.candidate_id,
                    hired_at=datetime.now(),
                )
            )
        elif new_status == ApplicationStatus.REJECTED:
            application.add_domain_event(
                CandidateRejected(
                    application_id=application.id,
                    job_id=application.job_id,
                    candidate_id=application.candidate_id,
                    rejected_at=datetime.now(),
                )
            )

        saved = self._app_repo.save(application)

        # Get related data
        job = self._job_repo.get_by_id(saved.job_id)
        candidate = self._candidate_repo.get_by_id(saved.candidate_id)

        return self._to_dto(
            saved,
            job.title if job else "",
            candidate,
        )

    def get_application(self, application_id: int) -> ApplicationDTO:
        """Get an application by ID."""
        application = self._app_repo.get_by_id(application_id)
        if not application:
            raise NotFoundError(
                f"Application with ID {application_id} not found"
            )

        job = self._job_repo.get_by_id(application.job_id)
        candidate = self._candidate_repo.get_by_id(application.candidate_id)

        return self._to_dto(
            application,
            job.title if job else "",
            candidate,
        )

    def get_applications_for_job(
        self,
        job_id: int,
        status: str | None = None,
    ) -> Sequence[ApplicationDTO]:
        """Get all applications for a job."""
        app_status = ApplicationStatus.from_string(status) if status else None
        applications = self._app_repo.get_by_job(job_id, status=app_status)

        job = self._job_repo.get_by_id(job_id)
        job_title = job.title if job else ""

        results = []
        for app in applications:
            candidate = self._candidate_repo.get_by_id(app.candidate_id)
            results.append(self._to_dto(app, job_title, candidate))

        return results

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

    def check_application_by_national_id(
        self,
        national_id: str,
        job_id: int,
    ) -> dict:
        """Check if a candidate has applied to a job by national ID."""
        candidate = self._candidate_repo.get_by_national_id(national_id)
        if not candidate:
            return {
                "candidate_exists": False,
                "has_applied": False,
            }

        existing = self._app_repo.get_by_job_and_candidate(
            job_id=job_id,
            candidate_id=candidate.id,
        )

        return {
            "candidate_exists": True,
            "has_applied": existing is not None,
            "candidate_id": candidate.id,
            "candidate_name": candidate.full_name,
        }

    def _to_dto(
        self,
        application: Application,
        job_title: str,
        candidate: Candidate | None,
    ) -> ApplicationDTO:
        """Convert entity to DTO."""
        return ApplicationDTO(
            id=application.id,
            job_id=application.job_id,
            job_title=job_title,
            candidate_id=application.candidate_id,
            candidate_name=candidate.full_name if candidate else "",
            candidate_email=candidate.email if candidate else "",
            cover_letter=application.cover_letter,
            status=application.status.value,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
        )

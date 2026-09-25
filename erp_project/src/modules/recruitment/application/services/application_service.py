"""
Application service for job applications.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.recruitment.application.authorization import (
    RecruitmentActor,
    RecruitmentAuthorizationPolicy,
)
from modules.recruitment.application.interfaces import (
    ApplicationDTO,
    ApplicationStatusDTO,
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
    IResumeStorage,
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
    """
    Command to submit (or resubmit) a job application from the public
    careers flow. The caller is anonymous: nothing here is trusted as proof
    of who the applicant is.
    """

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
    # The uploaded file itself; it is only stored once the submission has
    # been accepted, so a refused submission leaves nothing behind.
    resume_file: Any = None


@dataclass
class UpdateApplicationStatusCommand:
    """Command to update application status."""

    application_id: int
    new_status: str


@dataclass(frozen=True)
class SubmissionResult:
    """Outcome of a public submission: the application, and whether it is new."""

    application: ApplicationDTO
    created: bool


APPLICATION_DECIDED = (
    "This application has already been decided and can no longer be changed. "
    "Please contact HR if you need to discuss it."
)

APPLICANT_IDENTITY_CONFLICT = (
    "These details don't match our records for a previous application. "
    "If you have applied before, use the same ID number and email address "
    "you used then, or contact HR."
)


class ApplicationService:
    """
    Application service for job application operations.

    Internal operations (viewing applications, changing their status) take
    the acting RecruitmentActor and are authorized (REM-04) before anything is
    read or changed. The public careers operations - submit_application,
    has_applied, lookup_application_status - take no actor: they are public by
    design, and each discloses or changes only what that workflow needs.
    """

    def __init__(
        self,
        application_repository: IApplicationRepository,
        candidate_repository: ICandidateRepository,
        job_repository: IJobRepository,
        resume_storage: IResumeStorage | None = None,
        authorization_policy: RecruitmentAuthorizationPolicy | None = None,
    ) -> None:
        self._app_repo = application_repository
        self._candidate_repo = candidate_repository
        self._job_repo = job_repository
        self._resume_storage = resume_storage
        self._policy = authorization_policy or RecruitmentAuthorizationPolicy()
        self._processor = ApplicationProcessor()

    # ------------------------------------------------------------------
    # Public careers operations
    # ------------------------------------------------------------------

    def submit_application(self, command: SubmitApplicationCommand) -> SubmissionResult:
        """
        Submit a job application, or update the applicant's existing
        application for the same job.

        Matching an applicant, updating their application and modifying the
        canonical Candidate record are deliberately separate:

        - An existing Candidate is the same applicant only when *both* the
          national ID and the email agree with what is on record. Any other
          overlap is refused without saying whose record it collided with.
        - An existing Candidate record is never modified here. What the
          applicant sends (contact details, qualifications, experience,
          resume, cover letter) is recorded on the application itself.
        - Same applicant + same job updates that application; its review
          status is left alone. Once the application has been decided (Hired
          or Rejected) it is part of the hiring record and is refused instead.
        """
        job = self._job_repo.get_by_id(command.job_id)
        if not job:
            raise NotFoundError(f"Job with ID {command.job_id} not found")
        if not job.is_open:
            raise ValidationError("Cannot apply to a closed job")

        national_id = _normalize_national_id(command.national_id)
        candidate = self._match_existing_applicant(national_id, command.email)

        existing = None
        if candidate is not None:
            existing = self._app_repo.get_by_job_and_candidate(
                job_id=command.job_id,
                candidate_id=candidate.id,
            )
        if existing is not None and existing.is_decided:
            # Checked before the resume is stored, so a refusal leaves no file.
            raise ValidationError(APPLICATION_DECIDED, code="APPLICATION_DECIDED")

        resume_path = self._store_resume(command.resume_file)

        if candidate is None:
            candidate = self._create_candidate(command, national_id, resume_path)

        if existing is not None:
            existing.update_submission(
                cover_letter=command.cover_letter,
                phone=command.phone,
                address=command.address,
                qualifications=command.qualifications,
                experience=command.experience,
                resume_path=resume_path,
            )
            saved = self._app_repo.save(existing)
            return SubmissionResult(self._to_dto(saved, job.title, candidate), created=False)

        application = Application(
            id=None,  # assigned by the database on insert
            job_id=command.job_id,
            candidate_id=candidate.id,
            cover_letter=command.cover_letter,
            resume_path=resume_path,
            phone=command.phone,
            address=command.address,
            qualifications=command.qualifications,
            experience=command.experience,
        )
        saved = self._app_repo.save(application)
        saved.add_domain_event(
            ApplicationReceived(
                application_id=saved.id,
                job_id=saved.job_id,
                candidate_id=saved.candidate_id,
                applied_at=datetime.now(),
            )
        )
        return SubmissionResult(self._to_dto(saved, job.title, candidate), created=True)

    def has_applied(self, national_id: str, job_id: int) -> bool:
        """Whether whoever holds this national ID has applied to this job."""
        normalized = _normalize_national_id(national_id)
        candidate = self._candidate_repo.get_by_national_id(normalized) if normalized else None
        if not candidate:
            return False
        return self._app_repo.get_by_job_and_candidate(
            job_id=job_id,
            candidate_id=candidate.id,
        ) is not None

    def lookup_application_status(self, national_id: str) -> Sequence[ApplicationStatusDTO]:
        """
        Public status lookup by national ID.

        An unknown ID and a known ID with no applications give the same empty
        result, so the lookup does not confirm whether a candidate exists.
        """
        normalized = _normalize_national_id(national_id)
        candidate = self._candidate_repo.get_by_national_id(normalized) if normalized else None
        if not candidate:
            return []
        return self._status_dtos(candidate.id)

    # ------------------------------------------------------------------
    # Internal operations
    # ------------------------------------------------------------------

    def update_status(
        self, command: UpdateApplicationStatusCommand, actor: RecruitmentActor
    ) -> ApplicationDTO:
        """Update application status."""
        self._policy.authorize_review_applications(actor)
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

        # Notify the candidate by email if the status actually changed.
        if candidate and candidate.email and old_status != new_status:
            self._notify_candidate_status_change(
                candidate_email=candidate.email,
                job_title=job.title if job else "",
                new_status=new_status.value,
            )

        return self._to_dto(
            saved,
            job.title if job else "",
            candidate,
        )

    @staticmethod
    def _notify_candidate_status_change(
        candidate_email: str, job_title: str, new_status: str
    ) -> None:
        """Email the candidate that their application status changed."""
        from django.conf import settings
        from django.core.mail import send_mail

        try:
            send_mail(
                subject=f"Update on your application: {job_title}",
                message=(
                    f"Your application for '{job_title}' is now marked as "
                    f"'{new_status}'."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate_email],
                fail_silently=True,
            )
        except Exception:
            # A broken email config should never block a status update.
            pass

    def get_application(self, application_id: int, actor: RecruitmentActor) -> ApplicationDTO:
        """Get an application by ID."""
        self._policy.authorize_view_applications(actor)
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
        *,
        actor: RecruitmentActor,
    ) -> Sequence[ApplicationDTO]:
        """Get all applications for a job."""
        self._policy.authorize_view_applications(actor)
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
        actor: RecruitmentActor,
    ) -> Sequence[ApplicationStatusDTO]:
        """Get all applications for a candidate (internal)."""
        self._policy.authorize_view_applications(actor)
        return self._status_dtos(candidate_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_existing_applicant(self, national_id: str | None, email: str) -> Candidate | None:
        """
        The existing Candidate this submission belongs to, or None if the
        applicant is new.

        Raises ValidationError when the submission overlaps an existing
        Candidate (by national ID or email) without agreeing with it on both -
        e.g. someone else's national ID with a different email. The message
        is generic: it never reveals whose record was hit.
        """
        by_national_id = (
            self._candidate_repo.get_by_national_id(national_id) if national_id else None
        )
        by_email = self._candidate_repo.get_by_email(email) if email else None

        candidate = by_national_id or by_email
        if candidate is None:
            return None

        same_record = (
            by_national_id is None or by_email is None or by_national_id.id == by_email.id
        )
        same_identity = (
            _normalize_national_id(candidate.national_id) == national_id
            and (candidate.email or "").casefold() == (email or "").casefold()
        )
        if not (same_record and same_identity):
            raise ValidationError(APPLICANT_IDENTITY_CONFLICT, code="APPLICANT_IDENTITY_CONFLICT")
        return candidate

    def _create_candidate(
        self,
        command: SubmitApplicationCommand,
        national_id: str | None,
        resume_path: str | None,
    ) -> Candidate:
        """A new applicant's first submission becomes their Candidate record."""
        from datetime import date as date_type

        dob = None
        if command.date_of_birth:
            try:
                dob = date_type.fromisoformat(command.date_of_birth)
            except ValueError:
                pass

        candidate = Candidate(
            id=None,  # assigned by the database on insert
            first_name=command.first_name,
            last_name=command.last_name,
            email=command.email,
            national_id=national_id,
            phone=command.phone,
            address=command.address,
            date_of_birth=dob,
            qualifications=command.qualifications,
            experience=command.experience,
            resume_path=resume_path,
        )
        saved = self._candidate_repo.save(candidate)
        saved.add_domain_event(
            CandidateCreated(
                candidate_id=saved.id,
                email=saved.email,
                national_id=saved.national_id,
                created_at=datetime.now(),
            )
        )
        return saved

    def _store_resume(self, resume_file) -> str | None:
        if resume_file is None:
            return None
        if self._resume_storage is None:
            raise ValidationError("Resume uploads are not supported here")
        return self._resume_storage.save(resume_file)

    def _status_dtos(self, candidate_id: int) -> list[ApplicationStatusDTO]:
        results = []
        for app in self._app_repo.get_by_candidate(candidate_id):
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


def _normalize_national_id(national_id: str | None) -> str | None:
    """Blank national IDs are absent, not an empty-string identity."""
    normalized = (national_id or "").strip()
    return normalized or None

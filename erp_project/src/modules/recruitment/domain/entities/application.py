"""
JobApplication aggregate root.
"""

from datetime import datetime
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.recruitment.domain.value_objects import ApplicationStatus


class Application(AggregateRoot[int]):
    """
    Job application aggregate root.

    Represents a candidate's application for a specific job.
    """

    def __init__(
        self,
        id: int,
        job_id: int,
        candidate_id: int,
        cover_letter: str = "",
        status: ApplicationStatus = ApplicationStatus.PENDING,
        applied_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id)
        self.job_id = job_id
        self.candidate_id = candidate_id
        self.cover_letter = cover_letter
        self.status = status
        self.applied_at = applied_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self._validate()

    def _validate(self) -> None:
        """Validate application state."""
        if self.job_id is None or self.job_id <= 0:
            raise ValidationError("Valid job is required")
        if self.candidate_id is None or self.candidate_id <= 0:
            raise ValidationError("Valid candidate is required")

    @property
    def is_active(self) -> bool:
        """Check if application is still active (not final)."""
        return self.status.is_active

    @property
    def is_hired(self) -> bool:
        """Check if candidate was hired."""
        return self.status == ApplicationStatus.HIRED

    @property
    def is_rejected(self) -> bool:
        """Check if application was rejected."""
        return self.status == ApplicationStatus.REJECTED

    def shortlist(self) -> None:
        """Move application to shortlisted status."""
        if self.status.is_final:
            raise ValidationError(f"Cannot shortlist a {self.status.value} application")
        if self.status == ApplicationStatus.SHORTLISTED:
            raise ValidationError("Application is already shortlisted")
        self.status = ApplicationStatus.SHORTLISTED
        self.updated_at = datetime.now()

    def schedule_interview(self) -> None:
        """Move application to interview status."""
        if self.status.is_final:
            raise ValidationError(f"Cannot schedule interview for a {self.status.value} application")
        if self.status == ApplicationStatus.INTERVIEW:
            raise ValidationError("Interview is already scheduled")
        self.status = ApplicationStatus.INTERVIEW
        self.updated_at = datetime.now()

    def make_offer(self) -> None:
        """Move application to offered status."""
        if self.status.is_final:
            raise ValidationError(f"Cannot make offer for a {self.status.value} application")
        if self.status == ApplicationStatus.OFFERED:
            raise ValidationError("Offer has already been made")
        self.status = ApplicationStatus.OFFERED
        self.updated_at = datetime.now()

    def hire(self) -> None:
        """Mark candidate as hired."""
        if self.status == ApplicationStatus.HIRED:
            raise ValidationError("Candidate is already hired")
        if self.status == ApplicationStatus.REJECTED:
            raise ValidationError("Cannot hire a rejected application")
        self.status = ApplicationStatus.HIRED
        self.updated_at = datetime.now()

    def reject(self) -> None:
        """Reject the application."""
        if self.status == ApplicationStatus.HIRED:
            raise ValidationError("Cannot reject a hired candidate")
        if self.status == ApplicationStatus.REJECTED:
            raise ValidationError("Application is already rejected")
        self.status = ApplicationStatus.REJECTED
        self.updated_at = datetime.now()

    def update_cover_letter(self, cover_letter: str) -> None:
        """Update the cover letter."""
        self.cover_letter = cover_letter
        self.updated_at = datetime.now()

    def change_status(self, new_status: ApplicationStatus) -> None:
        """
        Change application status.

        Validates the transition is allowed.
        """
        if self.status.is_final and new_status != self.status:
            raise ValidationError(
                f"Cannot change status from {self.status.value} (final state)"
            )

        # Define valid transitions
        valid_transitions = {
            ApplicationStatus.PENDING: [
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.REJECTED,
            ],
            ApplicationStatus.SHORTLISTED: [
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFERED,
                ApplicationStatus.REJECTED,
            ],
            ApplicationStatus.INTERVIEW: [
                ApplicationStatus.OFFERED,
                ApplicationStatus.REJECTED,
            ],
            ApplicationStatus.OFFERED: [
                ApplicationStatus.HIRED,
                ApplicationStatus.REJECTED,
            ],
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValidationError(
                f"Invalid status transition from {self.status.value} to {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now()

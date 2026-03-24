"""
Recruitment domain services.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol, Sequence

from modules.recruitment.domain.entities import Application, Candidate, Job
from modules.recruitment.domain.value_objects import ApplicationStatus


class IApplicationProcessor(Protocol):
    """Interface for processing application status transitions."""

    def can_transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
    ) -> tuple[bool, str | None]:
        """
        Check if status transition is allowed.

        Returns tuple of (allowed, reason).
        """
        ...

    def process_transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
    ) -> None:
        """Process status transition."""
        ...


class IHiringService(Protocol):
    """
    Interface for hiring service.

    Creates an employee from a hired candidate.
    """

    def hire_candidate(
        self,
        application: Application,
        candidate: Candidate,
        job: Job,
    ) -> int:
        """
        Create employee from hired candidate.

        Returns the created employee ID.
        """
        ...


class IDuplicateApplicationChecker(Protocol):
    """Interface for checking duplicate applications."""

    def has_applied(
        self,
        candidate_id: int,
        job_id: int,
    ) -> bool:
        """Check if candidate has already applied to the job."""
        ...


class ApplicationProcessor(IApplicationProcessor):
    """Implementation of application status processor."""

    # Valid status transitions
    VALID_TRANSITIONS = {
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
        ApplicationStatus.HIRED: [],  # Final state
        ApplicationStatus.REJECTED: [],  # Final state
    }

    def can_transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
    ) -> tuple[bool, str | None]:
        """Check if status transition is allowed."""
        if application.status == new_status:
            return False, "Application is already in this status"

        if application.status.is_final:
            return False, f"Cannot change status from {application.status.value} (final state)"

        valid_next = self.VALID_TRANSITIONS.get(application.status, [])
        if new_status not in valid_next:
            return False, (
                f"Invalid transition from {application.status.value} "
                f"to {new_status.value}"
            )

        return True, None

    def process_transition(
        self,
        application: Application,
        new_status: ApplicationStatus,
    ) -> None:
        """Process status transition."""
        can_transition, reason = self.can_transition(application, new_status)
        if not can_transition:
            from shared.domain.exceptions import ValidationError
            raise ValidationError(reason)

        application.status = new_status
        application.updated_at = datetime.now()


class JobQualificationMatcher:
    """
    Domain service for matching candidate qualifications to job requirements.
    """

    def calculate_match_score(
        self,
        candidate: Candidate,
        job: Job,
    ) -> float:
        """
        Calculate a match score between candidate and job requirements.

        Returns score from 0.0 to 1.0.
        """
        if not job.qualifications:
            return 0.5  # No requirements defined

        candidate_quals = candidate.qualifications.lower()
        matched = 0
        total = len(job.qualifications)

        for qual in job.qualifications:
            if qual.lower() in candidate_quals:
                matched += 1

        return matched / total if total > 0 else 0.5

    def meets_minimum_requirements(
        self,
        candidate: Candidate,
        job: Job,
        minimum_score: float = 0.3,
    ) -> bool:
        """Check if candidate meets minimum job requirements."""
        return self.calculate_match_score(candidate, job) >= minimum_score


class ApplicationRankingService:
    """
    Domain service for ranking applications.
    """

    def __init__(self, qualification_matcher: JobQualificationMatcher) -> None:
        self._matcher = qualification_matcher

    def rank_applications(
        self,
        applications: Sequence[Application],
        candidates: dict[int, Candidate],
        job: Job,
    ) -> list[tuple[Application, float]]:
        """
        Rank applications by qualification match.

        Returns list of (application, score) tuples sorted by score descending.
        """
        ranked = []
        for app in applications:
            candidate = candidates.get(app.candidate_id)
            if candidate:
                score = self._matcher.calculate_match_score(candidate, job)
                ranked.append((app, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

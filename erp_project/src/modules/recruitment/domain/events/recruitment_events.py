"""
Recruitment domain events.
"""

from dataclasses import dataclass
from datetime import datetime

from shared.domain.base import DomainEvent


@dataclass(frozen=True)
class JobPosted(DomainEvent):
    """Event raised when a job is posted."""

    job_id: int
    title: str
    department_id: int
    is_internal: bool
    posted_at: datetime


@dataclass(frozen=True)
class JobClosed(DomainEvent):
    """Event raised when a job is closed."""

    job_id: int
    title: str
    closed_at: datetime


@dataclass(frozen=True)
class JobReopened(DomainEvent):
    """Event raised when a closed job is reopened."""

    job_id: int
    title: str
    reopened_at: datetime


@dataclass(frozen=True)
class ApplicationReceived(DomainEvent):
    """Event raised when an application is received."""

    application_id: int
    job_id: int
    candidate_id: int
    applied_at: datetime


@dataclass(frozen=True)
class ApplicationStatusChanged(DomainEvent):
    """Event raised when an application status changes."""

    application_id: int
    job_id: int
    candidate_id: int
    old_status: str
    new_status: str
    changed_at: datetime


@dataclass(frozen=True)
class CandidateShortlisted(DomainEvent):
    """Event raised when a candidate is shortlisted."""

    application_id: int
    job_id: int
    candidate_id: int
    shortlisted_at: datetime


@dataclass(frozen=True)
class CandidateInterviewScheduled(DomainEvent):
    """Event raised when a candidate interview is scheduled."""

    application_id: int
    job_id: int
    candidate_id: int
    scheduled_at: datetime


@dataclass(frozen=True)
class CandidateOffered(DomainEvent):
    """Event raised when an offer is made to a candidate."""

    application_id: int
    job_id: int
    candidate_id: int
    offered_at: datetime


@dataclass(frozen=True)
class CandidateHired(DomainEvent):
    """Event raised when a candidate is hired."""

    application_id: int
    job_id: int
    candidate_id: int
    hired_at: datetime


@dataclass(frozen=True)
class CandidateRejected(DomainEvent):
    """Event raised when a candidate is rejected."""

    application_id: int
    job_id: int
    candidate_id: int
    rejected_at: datetime


@dataclass(frozen=True)
class CandidateCreated(DomainEvent):
    """Event raised when a new candidate is created."""

    candidate_id: int
    email: str
    national_id: str | None
    created_at: datetime

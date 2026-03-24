"""
Recruitment domain events.
"""

from modules.recruitment.domain.events.recruitment_events import (
    ApplicationReceived,
    ApplicationStatusChanged,
    CandidateCreated,
    CandidateHired,
    CandidateInterviewScheduled,
    CandidateOffered,
    CandidateRejected,
    CandidateShortlisted,
    JobClosed,
    JobPosted,
    JobReopened,
)

__all__ = [
    "JobPosted",
    "JobClosed",
    "JobReopened",
    "ApplicationReceived",
    "ApplicationStatusChanged",
    "CandidateShortlisted",
    "CandidateInterviewScheduled",
    "CandidateOffered",
    "CandidateHired",
    "CandidateRejected",
    "CandidateCreated",
]

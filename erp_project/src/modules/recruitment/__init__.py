"""
Recruitment Module.

Manages job postings, candidates, and job applications.
Provides IRecruitmentProvider interface for cross-module integration with HR.
"""

from modules.recruitment.application import (
    ApplicationDTO,
    ApplicationStatusDTO,
    CandidateDTO,
    IRecruitmentProvider,
    JobDTO,
    RecruitmentProvider,
)
from modules.recruitment.domain import (
    Application,
    ApplicationStatus,
    Candidate,
    Job,
    JobStatus,
    SalaryRange,
)

__all__ = [
    # Domain
    "Job",
    "Candidate",
    "Application",
    "JobStatus",
    "ApplicationStatus",
    "SalaryRange",
    # Application
    "IRecruitmentProvider",
    "RecruitmentProvider",
    "JobDTO",
    "CandidateDTO",
    "ApplicationDTO",
    "ApplicationStatusDTO",
]

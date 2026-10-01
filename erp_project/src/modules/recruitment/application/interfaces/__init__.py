"""
Recruitment application interfaces.
"""

from modules.recruitment.application.interfaces.providers import (
    ApplicationDTO,
    ApplicationStatusDTO,
    CandidateDTO,
    IRecruitmentProvider,
    JobDTO,
)
from modules.recruitment.application.interfaces.repositories import (
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
)

__all__ = [
    # Repositories
    "IJobRepository",
    "ICandidateRepository",
    "IApplicationRepository",
    # Providers
    "IRecruitmentProvider",
    # DTOs
    "JobDTO",
    "CandidateDTO",
    "ApplicationDTO",
    "ApplicationStatusDTO",
]

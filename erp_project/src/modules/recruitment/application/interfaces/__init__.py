"""
Recruitment application interfaces.
"""

from modules.recruitment.application.interfaces.providers import (
    ApplicationDTO,
    ApplicationStatusDTO,
    CandidateDTO,
    IRecruitmentProvider,
    JobDTO,
    PublicJobDTO,
)
from modules.recruitment.application.interfaces.repositories import (
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
)
from modules.recruitment.application.interfaces.storage import IResumeStorage

__all__ = [
    # Repositories
    "IJobRepository",
    "ICandidateRepository",
    "IApplicationRepository",
    # Providers
    "IRecruitmentProvider",
    "IResumeStorage",
    # DTOs
    "JobDTO",
    "PublicJobDTO",
    "CandidateDTO",
    "ApplicationDTO",
    "ApplicationStatusDTO",
]

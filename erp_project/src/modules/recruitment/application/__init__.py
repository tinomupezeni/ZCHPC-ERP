"""
Recruitment application layer.

Contains application services, interfaces, and DTOs.
"""

from modules.recruitment.application.interfaces import (
    ApplicationDTO,
    ApplicationStatusDTO,
    CandidateDTO,
    IApplicationRepository,
    ICandidateRepository,
    IJobRepository,
    IRecruitmentProvider,
    JobDTO,
)
from modules.recruitment.application.services import (
    ApplicationService,
    CreateJobCommand,
    JobService,
    RecruitmentProvider,
    SubmitApplicationCommand,
    UpdateApplicationStatusCommand,
    UpdateJobCommand,
)

__all__ = [
    # Interfaces
    "IJobRepository",
    "ICandidateRepository",
    "IApplicationRepository",
    "IRecruitmentProvider",
    # DTOs
    "JobDTO",
    "CandidateDTO",
    "ApplicationDTO",
    "ApplicationStatusDTO",
    # Services
    "JobService",
    "ApplicationService",
    "RecruitmentProvider",
    # Commands
    "CreateJobCommand",
    "UpdateJobCommand",
    "SubmitApplicationCommand",
    "UpdateApplicationStatusCommand",
]

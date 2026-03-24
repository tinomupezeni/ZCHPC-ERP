"""
Recruitment module models.

Re-exports models from infrastructure layer for Django discovery.
"""

from modules.recruitment.infrastructure.persistence.models import (
    Candidate,
    Job,
    JobApplication,
)

__all__ = [
    "Job",
    "Candidate",
    "JobApplication",
]

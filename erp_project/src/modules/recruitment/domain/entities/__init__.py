"""
Recruitment domain entities.
"""

from modules.recruitment.domain.entities.application import Application
from modules.recruitment.domain.entities.candidate import Candidate
from modules.recruitment.domain.entities.job import Job

__all__ = [
    "Job",
    "Candidate",
    "Application",
]

"""
Recruitment file-storage port.
"""

from typing import Protocol


class IResumeStorage(Protocol):
    """Persists an uploaded resume and returns its storage path."""

    def save(self, uploaded_file) -> str:
        ...

"""
Candidate aggregate root.
"""

from datetime import date, datetime
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


class Candidate(AggregateRoot[int]):
    """
    Candidate aggregate root.

    Represents a person who applies for jobs.
    """

    def __init__(
        self,
        id: int,
        first_name: str,
        last_name: str,
        email: str,
        national_id: Optional[str] = None,
        phone: str = "",
        address: str = "",
        date_of_birth: Optional[date] = None,
        resume_path: Optional[str] = None,
        qualifications: str = "",
        experience: str = "",
        notes: str = "",
        created_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.national_id = national_id
        self.phone = phone
        self.address = address
        self.date_of_birth = date_of_birth
        self.resume_path = resume_path
        self.qualifications = qualifications
        self.experience = experience
        self.notes = notes
        self.created_at = created_at or datetime.now()
        self._validate()

    def _validate(self) -> None:
        """Validate candidate state."""
        if not self.first_name or not self.first_name.strip():
            raise ValidationError("First name is required")
        if not self.last_name or not self.last_name.strip():
            raise ValidationError("Last name is required")
        if not self.email or "@" not in self.email:
            raise ValidationError("Valid email is required")

    @property
    def full_name(self) -> str:
        """Get candidate's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def has_resume(self) -> bool:
        """Check if candidate has uploaded a resume."""
        return bool(self.resume_path)

    def update_contact(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        """Update contact information."""
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
        self._validate()

    def update_personal(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        national_id: Optional[str] = None,
    ) -> None:
        """Update personal information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        if national_id is not None:
            self.national_id = national_id
        self._validate()

    def update_qualifications(
        self,
        qualifications: Optional[str] = None,
        experience: Optional[str] = None,
    ) -> None:
        """Update qualifications and experience."""
        if qualifications is not None:
            self.qualifications = qualifications
        if experience is not None:
            self.experience = experience

    def set_resume(self, resume_path: Optional[str]) -> None:
        """Set resume file path."""
        self.resume_path = resume_path

    def add_notes(self, notes: str) -> None:
        """Add notes to candidate."""
        if self.notes:
            self.notes = f"{self.notes}\n{notes}"
        else:
            self.notes = notes

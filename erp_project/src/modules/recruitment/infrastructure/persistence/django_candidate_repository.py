"""
Django ORM implementation of ICandidateRepository.
"""

from typing import Sequence

from modules.recruitment.infrastructure.persistence.models import Candidate as CandidateModel

from modules.recruitment.application.interfaces import ICandidateRepository
from modules.recruitment.domain.entities import Candidate


class DjangoCandidateRepository(ICandidateRepository):
    """Django ORM implementation of candidate repository."""

    def get_by_id(self, candidate_id: int) -> Candidate | None:
        """Get candidate by ID."""
        try:
            model = CandidateModel.objects.get(id=candidate_id)
            return self._to_entity(model)
        except CandidateModel.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Candidate | None:
        """Get candidate by email."""
        try:
            model = CandidateModel.objects.get(email=email)
            return self._to_entity(model)
        except CandidateModel.DoesNotExist:
            return None

    def get_by_national_id(self, national_id: str) -> Candidate | None:
        """Get candidate by national ID."""
        try:
            model = CandidateModel.objects.get(id_number=national_id)
            return self._to_entity(model)
        except CandidateModel.DoesNotExist:
            return None

    def get_all(self) -> Sequence[Candidate]:
        """Get all candidates."""
        queryset = CandidateModel.objects.all()
        return [self._to_entity(model) for model in queryset]

    def save(self, candidate: Candidate) -> Candidate:
        """Save candidate."""
        model, created = CandidateModel.objects.update_or_create(
            id=candidate.id,
            defaults={
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "email": candidate.email,
                "id_number": candidate.national_id,
                "phone": candidate.phone,
                "address": candidate.address,
                "date_of_birth": candidate.date_of_birth,
                "qualifications": candidate.qualifications,
                "experience": candidate.experience,
                "notes": candidate.notes,
            },
        )
        # Handle resume separately if needed
        if candidate.resume_path and not created:
            # Only update resume if it changed
            if model.resume.name != candidate.resume_path:
                model.resume = candidate.resume_path
                model.save()

        return self._to_entity(model)

    def delete(self, candidate_id: int) -> None:
        """Delete candidate."""
        CandidateModel.objects.filter(id=candidate_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = CandidateModel.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, model: CandidateModel) -> Candidate:
        """Convert Django model to domain entity."""
        resume_path = None
        if model.resume:
            resume_path = model.resume.name

        return Candidate(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            national_id=model.id_number,
            phone=model.phone or "",
            address=model.address or "",
            date_of_birth=model.date_of_birth,
            resume_path=resume_path,
            qualifications=model.qualifications or "",
            experience=model.experience or "",
            notes=model.notes or "",
            created_at=model.created_at,
        )

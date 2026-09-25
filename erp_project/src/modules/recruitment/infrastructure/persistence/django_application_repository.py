"""
Django ORM implementation of IApplicationRepository.
"""

from typing import Sequence

from modules.recruitment.infrastructure.persistence._save import insert_or_update
from modules.recruitment.infrastructure.persistence.models import JobApplication as ApplicationModel

from modules.recruitment.application.interfaces import IApplicationRepository
from modules.recruitment.domain.entities import Application
from modules.recruitment.domain.value_objects import ApplicationStatus


class DjangoApplicationRepository(IApplicationRepository):
    """Django ORM implementation of application repository."""

    def get_by_id(self, application_id: int) -> Application | None:
        """Get application by ID."""
        try:
            model = ApplicationModel.objects.select_related(
                "job", "candidate"
            ).get(id=application_id)
            return self._to_entity(model)
        except ApplicationModel.DoesNotExist:
            return None

    def get_by_job(
        self,
        job_id: int,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get applications for a job."""
        queryset = ApplicationModel.objects.select_related(
            "job", "candidate"
        ).filter(job_id=job_id)

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return [self._to_entity(model) for model in queryset]

    def get_by_candidate(
        self,
        candidate_id: int,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get applications by candidate."""
        queryset = ApplicationModel.objects.select_related(
            "job", "candidate"
        ).filter(candidate_id=candidate_id)

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return [self._to_entity(model) for model in queryset]

    def get_by_job_and_candidate(
        self,
        job_id: int,
        candidate_id: int,
    ) -> Application | None:
        """Get application by job and candidate."""
        try:
            model = ApplicationModel.objects.select_related(
                "job", "candidate"
            ).get(job_id=job_id, candidate_id=candidate_id)
            return self._to_entity(model)
        except ApplicationModel.DoesNotExist:
            return None

    def get_all(
        self,
        status: ApplicationStatus | None = None,
    ) -> Sequence[Application]:
        """Get all applications."""
        queryset = ApplicationModel.objects.select_related("job", "candidate").all()

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return [self._to_entity(model) for model in queryset]

    def save(self, application: Application) -> Application:
        """Insert a new application (id None) or update its existing row."""
        model = insert_or_update(
            ApplicationModel,
            application.id,
            {
                "job_id": application.job_id,
                "candidate_id": application.candidate_id,
                "cover_letter": application.cover_letter,
                "status": application.status.value,
                "resume": application.resume_path or None,
                "phone": application.phone,
                "address": application.address,
                "qualifications": application.qualifications,
                "experience": application.experience,
            },
        )
        # Reload with relationships
        model = ApplicationModel.objects.select_related("job", "candidate").get(
            id=model.id
        )
        return self._to_entity(model)

    def delete(self, application_id: int) -> None:
        """Delete application."""
        ApplicationModel.objects.filter(id=application_id).delete()

    def count_by_job(
        self,
        job_id: int,
        status: ApplicationStatus | None = None,
    ) -> int:
        """Count applications for a job."""
        queryset = ApplicationModel.objects.filter(job_id=job_id)

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return queryset.count()

    def _to_entity(self, model: ApplicationModel) -> Application:
        """Convert Django model to domain entity."""
        status = ApplicationStatus.from_string(model.status)

        return Application(
            id=model.id,
            job_id=model.job_id,
            candidate_id=model.candidate_id,
            cover_letter=model.cover_letter or "",
            status=status,
            applied_at=model.applied_on,
            updated_at=model.updated_at or model.applied_on,
            resume_path=model.resume.name or None,
            phone=model.phone or "",
            address=model.address or "",
            qualifications=model.qualifications or "",
            experience=model.experience or "",
        )

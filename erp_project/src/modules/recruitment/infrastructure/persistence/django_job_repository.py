"""
Django ORM implementation of IJobRepository.
"""

from decimal import Decimal
from typing import Sequence

from django.db.models import Q

from modules.recruitment.infrastructure.persistence.models import Job as JobModel

from modules.recruitment.application.interfaces import IJobRepository
from modules.recruitment.domain.entities import Job
from modules.recruitment.domain.value_objects import JobStatus, SalaryRange


class DjangoJobRepository(IJobRepository):
    """Django ORM implementation of job repository."""

    def get_by_id(self, job_id: int) -> Job | None:
        """Get job by ID."""
        try:
            model = JobModel.objects.select_related(
                "department", "position"
            ).get(id=job_id)
            return self._to_entity(model)
        except JobModel.DoesNotExist:
            return None

    def get_all(
        self,
        status: JobStatus | None = None,
        department_id: int | None = None,
        is_internal: bool | None = None,
    ) -> Sequence[Job]:
        """Get all jobs with optional filters."""
        queryset = JobModel.objects.select_related("department", "position").all()

        if status is not None:
            queryset = queryset.filter(status=status.value)
        if department_id is not None:
            queryset = queryset.filter(department_id=department_id)
        if is_internal is not None:
            queryset = queryset.filter(is_internal=is_internal)

        return [self._to_entity(model) for model in queryset]

    def get_open_jobs(self, is_internal: bool | None = None) -> Sequence[Job]:
        """Get all open jobs."""
        queryset = JobModel.objects.select_related(
            "department", "position"
        ).filter(status="Open")

        if is_internal is not None:
            queryset = queryset.filter(is_internal=is_internal)

        return [self._to_entity(model) for model in queryset]

    def get_public_jobs(self) -> Sequence[Job]:
        """Get all public (non-internal, open) jobs."""
        queryset = JobModel.objects.select_related(
            "department", "position"
        ).filter(status="Open", is_internal=False)

        return [self._to_entity(model) for model in queryset]

    def save(self, job: Job) -> Job:
        """Save job."""
        model, created = JobModel.objects.update_or_create(
            id=job.id,
            defaults={
                "title": job.title,
                "department_id": job.department_id,
                "position_id": job.position_id,
                "status": job.status.value,
                "location": job.location,
                "reports_to": job.reports_to,
                "salary_usd_min": job.salary_range.usd_min,
                "salary_usd_max": job.salary_range.usd_max,
                "salary_zig_min": job.salary_range.zig_min,
                "salary_zig_max": job.salary_range.zig_max,
                "is_internal": job.is_internal,
                "description": job.description,
                "responsibilities": list(job.responsibilities),
                "qualifications": list(job.qualifications),
                "competencies": list(job.competencies),
                "application_process": job.application_process,
                "contact_email": job.contact_email,
                "notes": job.notes,
                "posted_date": job.posted_date,
            },
        )
        # Reload with relationships
        model = JobModel.objects.select_related("department", "position").get(
            id=model.id
        )
        return self._to_entity(model)

    def delete(self, job_id: int) -> None:
        """Delete job."""
        JobModel.objects.filter(id=job_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = JobModel.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def search(
        self,
        query: str,
        status: JobStatus | None = None,
    ) -> Sequence[Job]:
        """Search jobs by title or description."""
        queryset = JobModel.objects.select_related("department", "position").filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

        if status is not None:
            queryset = queryset.filter(status=status.value)

        return [self._to_entity(model) for model in queryset]

    def _to_entity(self, model: JobModel) -> Job:
        """Convert Django model to domain entity."""
        salary_range = SalaryRange(
            usd_min=Decimal(str(model.salary_usd_min)) if model.salary_usd_min else None,
            usd_max=Decimal(str(model.salary_usd_max)) if model.salary_usd_max else None,
            zig_min=Decimal(str(model.salary_zig_min)) if model.salary_zig_min else None,
            zig_max=Decimal(str(model.salary_zig_max)) if model.salary_zig_max else None,
        )

        status = JobStatus.from_string(model.status)

        return Job(
            id=model.id,
            title=model.title,
            department_id=model.department_id,
            position_id=model.position_id,
            status=status,
            location=model.location or "Harare",
            reports_to=model.reports_to or "ZCHPC Director",
            salary_range=salary_range,
            is_internal=model.is_internal,
            description=model.description or "",
            responsibilities=model.responsibilities or [],
            qualifications=model.qualifications or [],
            competencies=model.competencies or [],
            application_process=model.application_process or "",
            contact_email=model.contact_email or "hroffice@zchpc.ac.zw",
            notes=model.notes or "",
            posted_date=model.posted_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

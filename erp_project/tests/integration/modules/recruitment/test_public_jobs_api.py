"""
Regression test: the public careers API must be reachable without
authentication.

RBACMiddleware fails closed on every /api/ path unless it's explicitly
listed in EXEMPT_PATHS, regardless of a view's own AllowAny permission
class. /api/v2/portal/public/ was exempted, but /api/v2/recruitment/public/
(the module the careers page actually calls - see jobs.service.ts) wasn't,
so every anonymous visitor got 401 on job listings and applications.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestPublicJobsAreAnonymouslyReachable:
    def test_public_job_list_does_not_require_authentication(self):
        response = APIClient().get("/api/v2/recruitment/public/jobs/")
        assert response.status_code == status.HTTP_200_OK

    def test_public_application_status_does_not_require_authentication(self):
        response = APIClient().post(
            "/api/v2/recruitment/public/applications/status/",
            {"id_number": "63-000000A00"},
            format="json",
        )
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPublicJobsIncludeInternalPostings:
    """
    The public careers page intentionally shows every open job, internal or
    not - internal-only postings still need to be discoverable by the public
    audience this ERP serves (ZCHPC staff, Resident Innovators, Interns,
    Volunteer Experts aren't necessarily logged into the admin dashboard).
    """

    def _create_job(self, *, title, is_internal, status_value="Open"):
        from modules.hr.infrastructure.persistence.models import Department
        from modules.recruitment.infrastructure.persistence.models import Job

        department, _ = Department.objects.get_or_create(name="Systems Support", defaults={"description": ""})
        return Job.objects.create(
            title=title, status=status_value, is_internal=is_internal, department=department
        )

    def test_public_list_includes_internal_and_external_open_jobs(self):
        self._create_job(title="Internal Role", is_internal=True)
        self._create_job(title="External Role", is_internal=False)

        response = APIClient().get("/api/v2/recruitment/public/jobs/")
        assert response.status_code == status.HTTP_200_OK
        titles = {job["title"] for job in response.json()}
        assert titles == {"Internal Role", "External Role"}

    def test_public_list_excludes_closed_jobs(self):
        self._create_job(title="Closed Internal Role", is_internal=True, status_value="Closed")

        response = APIClient().get("/api/v2/recruitment/public/jobs/")
        assert response.status_code == status.HTTP_200_OK
        titles = {job["title"] for job in response.json()}
        assert "Closed Internal Role" not in titles

    def test_public_detail_view_reachable_for_internal_job(self):
        job = self._create_job(title="Internal Role", is_internal=True)

        response = APIClient().get(f"/api/v2/recruitment/public/jobs/{job.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Internal Role"

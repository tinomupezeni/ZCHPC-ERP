"""
Regression test for GET /api/v2/recruitment/jobs/ (admin job list).

DRF's BooleanField has HTML-checkbox semantics: given a QueryDict (which is
what every real GET request's query_params is) and a missing key, it
silently defaults to False instead of "not provided". JobQuerySerializer.internal
hit exactly this, so any request without ?internal= implicitly filtered to
is_internal=False and hid every internal job.
"""
import pytest
from rest_framework import status

pytestmark = pytest.mark.integration

LIST_URL = "/api/v2/recruitment/jobs/"


@pytest.fixture
def sample_department(db):
    from modules.hr.infrastructure.persistence.models import Department

    return Department.objects.create(name="Systems Support", description="")


@pytest.mark.django_db
class TestJobListAPI:
    def _create_job(self, admin_client, sample_department, *, title, is_internal):
        payload = {
            "title": title,
            "status": "Open",
            "location": "Harare",
            "is_internal": is_internal,
            "department_id": sample_department.id,
        }
        response = admin_client.post(LIST_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.content
        return response.json()["id"]

    def test_list_with_no_query_params_returns_internal_and_external_jobs(self, admin_client, sample_department):
        self._create_job(admin_client, sample_department, title="Internal Role", is_internal=True)
        self._create_job(admin_client, sample_department, title="External Role", is_internal=False)

        response = admin_client.get(LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        titles = {job["title"] for job in response.json()}
        assert titles == {"Internal Role", "External Role"}

    def test_list_filtered_internal_true(self, admin_client, sample_department):
        self._create_job(admin_client, sample_department, title="Internal Role", is_internal=True)
        self._create_job(admin_client, sample_department, title="External Role", is_internal=False)

        response = admin_client.get(LIST_URL, {"internal": "true"})
        assert response.status_code == status.HTTP_200_OK
        titles = [job["title"] for job in response.json()]
        assert titles == ["Internal Role"]

    def test_list_filtered_internal_false(self, admin_client, sample_department):
        self._create_job(admin_client, sample_department, title="Internal Role", is_internal=True)
        self._create_job(admin_client, sample_department, title="External Role", is_internal=False)

        response = admin_client.get(LIST_URL, {"internal": "false"})
        assert response.status_code == status.HTTP_200_OK
        titles = [job["title"] for job in response.json()]
        assert titles == ["External Role"]

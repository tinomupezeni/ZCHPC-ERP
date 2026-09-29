"""
REM-04: internal recruitment authorization.

RBACMiddleware lets anyone holding *some* ``recruitment.*`` permission reach
every recruitment route. What they may actually do there is decided by the
recruitment application services against four administrator-assigned
capabilities - no role names, no department scoping.

ROUTE below is a permission that gets a caller past the middleware while
granting no recruitment capability, which is how these tests prove the
service layer (not the middleware) is what refuses.
"""
import itertools

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from modules.recruitment.api.views import get_application_service, get_job_service
from modules.recruitment.application.authorization import (
    RecruitmentActor,
    RecruitmentPermissions as R,
)
from modules.recruitment.application.services import UpdateApplicationStatusCommand
from modules.recruitment.infrastructure.persistence.models import Candidate, Job, JobApplication
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.integration

User = get_user_model()
ROUTE = "recruitment.access"  # reaches /api/v2/recruitment/, grants no capability
_numbers = itertools.count(1)
BASE = "/api/v2/recruitment"


def jwt(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def client_with(*permissions):
    n = next(_numbers)
    role = Role.objects.create(name=f"RECRUIT_TEST_{n}", permissions=list(permissions))
    user = User.objects.create_user(email=f"recruit{n}@zchpc.test", password="Pass12345!")
    Employees.objects.create(
        user=user, first_name="Actor", surname=str(n), email=f"recruit{n}@zchpc.test",
        employee_id=f"RCT{n:04d}", role=role,
    )
    return jwt(user)


@pytest.fixture
def records(db):
    department = Department.objects.create(name="Recruitment Test Dept", description="")
    job = Job.objects.create(title="Open Role", status="Open", department=department)
    spare = Job.objects.create(title="Spare Draft", status="Draft", department=department)
    candidate = Candidate.objects.create(
        id_number="63-222222B22", first_name="Private", last_name="Candidate",
        email="private.candidate@example.com",
    )
    application = JobApplication.objects.create(
        job=job, candidate=candidate, cover_letter="CONFIDENTIAL", status="Pending"
    )
    return {"department": department, "job": job, "spare": spare, "application": application}


# (method, url builder, payload, required capability)
def _endpoints(r):
    job, spare, app = r["job"].id, r["spare"].id, r["application"].id
    create = {"title": "New Role", "department_id": r["department"].id}
    return [
        ("get", f"{BASE}/jobs/", None, R.JOB_VIEW),
        ("get", f"{BASE}/jobs/?search=Role", None, R.JOB_VIEW),
        ("post", f"{BASE}/jobs/", create, R.JOB_MANAGE),
        ("get", f"{BASE}/jobs/{job}/", None, R.JOB_VIEW),
        ("patch", f"{BASE}/jobs/{job}/", {"title": "Renamed"}, R.JOB_MANAGE),
        ("delete", f"{BASE}/jobs/{spare}/", None, R.JOB_MANAGE),
        ("post", f"{BASE}/jobs/{spare}/publish/", None, R.JOB_MANAGE),
        ("post", f"{BASE}/jobs/{job}/close/", None, R.JOB_MANAGE),
        ("get", f"{BASE}/jobs/{job}/applications/", None, R.APPLICATION_VIEW),
        ("get", f"{BASE}/applications/{app}/", None, R.APPLICATION_VIEW),
        ("post", f"{BASE}/applications/{app}/status/", {"status": "Shortlisted"}, R.APPLICATION_REVIEW),
    ]


ENDPOINT_IDS = [
    "list", "search", "create", "detail", "update", "delete", "publish", "close",
    "job-applications", "application-detail", "application-status",
]
ALL_CAPABILITIES = [R.JOB_VIEW, R.JOB_MANAGE, R.APPLICATION_VIEW, R.APPLICATION_REVIEW]


def _call(client, method, url, payload):
    return getattr(client, method)(url, payload, format="json") if payload else getattr(client, method)(url)


@pytest.mark.django_db
class TestCapabilityMatrix:
    @pytest.mark.parametrize("index", range(11), ids=ENDPOINT_IDS)
    def test_route_reachability_alone_is_refused_by_the_service(self, records, index):
        method, url, payload, _ = _endpoints(records)[index]
        response = _call(client_with(ROUTE), method, url, payload)
        assert response.status_code == 403
        # The refusal comes from the recruitment policy, not RBACMiddleware.
        assert response.json()["code"] == "RECRUITMENT_PERMISSION_DENIED"

    @pytest.mark.parametrize("index", range(11), ids=ENDPOINT_IDS)
    def test_required_capability_grants_the_operation(self, records, index):
        method, url, payload, capability = _endpoints(records)[index]
        response = _call(client_with(ROUTE, capability), method, url, payload)
        assert response.status_code in (200, 201, 204), response.content

    @pytest.mark.parametrize("index", range(11), ids=ENDPOINT_IDS)
    def test_every_other_capability_is_refused(self, records, index):
        method, url, payload, capability = _endpoints(records)[index]
        others = [c for c in ALL_CAPABILITIES if c != capability]
        response = _call(client_with(ROUTE, *others), method, url, payload)
        assert response.status_code == 403

    def test_view_capability_does_not_permit_mutation(self, records):
        client = client_with(R.JOB_VIEW, R.APPLICATION_VIEW)
        app = records["application"]
        assert client.get(f"{BASE}/applications/{app.id}/").status_code == 200
        assert client.post(
            f"{BASE}/applications/{app.id}/status/", {"status": "Shortlisted"}, format="json"
        ).status_code == 403
        assert client.delete(f"{BASE}/jobs/{records['spare'].id}/").status_code == 403
        app.refresh_from_db()
        assert app.status == "Pending"
        assert Job.objects.filter(pk=records["spare"].pk).exists()

    def test_missing_record_is_403_not_404_without_the_capability(self, records):
        client = client_with(ROUTE)
        assert client.get(f"{BASE}/applications/999999/").status_code == 403
        assert client.get(f"{BASE}/jobs/999999/").status_code == 403


@pytest.mark.django_db
class TestPreservedAccess:
    @pytest.mark.parametrize("grant", [["recruitment.*"], ["*"]], ids=["module-wildcard", "full-wildcard"])
    @pytest.mark.parametrize("index", range(11), ids=ENDPOINT_IDS)
    def test_wildcards_keep_full_access(self, records, grant, index):
        method, url, payload, _ = _endpoints(records)[index]
        response = _call(client_with(*grant), method, url, payload)
        assert response.status_code in (200, 201, 204), response.content

    def test_unlinked_superuser_keeps_full_access(self, records):
        superuser = User.objects.create_superuser(email="root@zchpc.test", password="Pass12345!")
        client = jwt(superuser)
        app = records["application"]
        assert client.get(f"{BASE}/applications/{app.id}/").status_code == 200
        assert client.post(
            f"{BASE}/applications/{app.id}/status/", {"status": "Shortlisted"}, format="json"
        ).status_code == 200

    def test_employee_without_recruitment_permissions_is_stopped_at_the_gate(self, records):
        client = client_with("portal.*", "identity.*", "self.*")
        response = client.get(f"{BASE}/applications/{records['application'].id}/")
        assert response.status_code == 403
        assert "CONFIDENTIAL" not in response.content.decode()

    def test_anonymous_is_rejected(self, records):
        assert APIClient().get(f"{BASE}/applications/{records['application'].id}/").status_code == 401


@pytest.mark.django_db
class TestServiceLayerEnforcement:
    """The services refuse on their own, whatever the HTTP layer did."""

    def actor(self, *permissions):
        return RecruitmentActor(permissions=PermissionSet.from_list(list(permissions)))

    def test_job_service_requires_capabilities(self, records):
        service = get_job_service()
        with pytest.raises(AuthorizationError):
            service.get_job(records["job"].id, self.actor(ROUTE))
        with pytest.raises(AuthorizationError):
            service.get_all_jobs(actor=self.actor(R.JOB_MANAGE))
        with pytest.raises(AuthorizationError):
            service.close_job(records["job"].id, self.actor(R.JOB_VIEW))
        assert service.get_job(records["job"].id, self.actor(R.JOB_VIEW)).title == "Open Role"

    def test_application_service_requires_capabilities(self, records):
        service = get_application_service()
        app_id = records["application"].id
        with pytest.raises(AuthorizationError):
            service.get_application(app_id, self.actor(R.JOB_VIEW))
        with pytest.raises(AuthorizationError):
            service.update_status(
                UpdateApplicationStatusCommand(app_id, "Shortlisted"), self.actor(R.APPLICATION_VIEW)
            )
        with pytest.raises(AuthorizationError):
            service.get_candidate_applications(records["application"].candidate_id, self.actor(ROUTE))
        assert service.get_application(app_id, self.actor(R.APPLICATION_VIEW)).id == app_id

    def test_anonymous_actor_is_unauthenticated(self, records):
        with pytest.raises(AuthorizationError) as excinfo:
            get_job_service().get_all_jobs(actor=RecruitmentActor.anonymous())
        assert excinfo.value.code == "UNAUTHENTICATED"

    def test_internal_methods_cannot_be_called_without_an_actor(self, records):
        with pytest.raises(TypeError):
            get_job_service().get_job(records["job"].id)
        with pytest.raises(TypeError):
            get_application_service().get_application(records["application"].id)

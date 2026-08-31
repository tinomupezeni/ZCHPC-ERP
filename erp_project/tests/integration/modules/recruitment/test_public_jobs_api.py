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

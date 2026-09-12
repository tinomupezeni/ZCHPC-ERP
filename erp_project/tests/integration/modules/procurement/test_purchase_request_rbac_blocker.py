"""
Executable documentation of the middleware/RBAC conflict blocking Slice 5.

Deliberately kept out of test_purchase_request_api.py so that it runs with the
full middleware stack, including the legacy URL gates those tests remove.
"""

import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestRbacMiddlewareBlocker:
    """
    Executable documentation of the middleware/RBAC conflict.

    RBACMiddleware authorizes /api/v2/procurement/ from the hard-coded
    ROLE_PERMISSIONS map, which does not know about hr.Role.permissions. A
    department head with every Slice 4 capability is still refused at the URL
    gate, so the workflow is unusable for most roles until this is resolved.

    This test runs WITHOUT the fixture that removes the legacy gates. If it
    starts failing, the blocker has been fixed and this test should be removed.
    """

    def test_department_head_is_blocked_by_the_legacy_url_gate(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"

"""
Slice 3 - Purchase Request notifications, end to end.

Runs against the full stack (real HTTP, real login, real event bus, real
DjangoNotificationRepository) so this is the only place that actually proves
procurement's published domain events reach modules.portal.event_handlers and
land in the database - the unit tests for the use cases and the handlers each
mock the other side of that boundary.

Shared fixtures (org, login, payload, create_and_submit) live in
tests/integration/modules/procurement/e2e/conftest.py.
"""

from rest_framework import status

import pytest

from modules.portal.infrastructure.persistence.models import Notification
from tests.integration.modules.procurement.e2e.conftest import (
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db


def _notifications_for(employee):
    return Notification.objects.filter(employee_id=employee.id).order_by("-created_at")


class TestRejectionNotification:
    def test_rejection_notifies_the_requester(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)

        response = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Specification is incomplete"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_notifications_for(org["requester"]))
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.notification_type == "purchase_request_rejected"
        assert notification.is_read is False
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == request_id
        assert response.data["requisition_number"] in notification.message
        assert "Specification is incomplete" in notification.message

    def test_rejector_is_not_the_one_notified(self, login, org, payload):
        """The department head who rejected gets nothing - only the requester does."""
        request_id = create_and_submit(login, org, payload)

        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Not needed"},
            format="json",
        )

        assert _notifications_for(org["department_head"]).count() == 0
        assert _notifications_for(org["requester"]).count() == 1

    def test_retrying_a_rejection_does_not_duplicate_the_notification(
        self, login, org, payload
    ):
        """
        Idempotency: a client retry (double-click, network retry) against an
        already-rejected request must fail, not create a second notification.
        """
        request_id = create_and_submit(login, org, payload)
        client = login(org["department_head"])

        first = client.post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Specification is incomplete"},
            format="json",
        )
        assert first.status_code == status.HTTP_200_OK
        assert _notifications_for(org["requester"]).count() == 1

        retry = client.post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Specification is incomplete"},
            format="json",
        )
        assert retry.status_code != status.HTTP_200_OK
        assert _notifications_for(org["requester"]).count() == 1


class TestProcessedNotification:
    def _advance_to_procurement(self, login, org, request_id):
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")
        login(org["gm"]).post(f"{REQUESTS_URL}{request_id}/gm/recommend/")
        login(org["director"]).post(f"{REQUESTS_URL}{request_id}/director/approve/")

    def test_processing_notifies_the_requester(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        self._advance_to_procurement(login, org, request_id)

        response = login(org["procurement"]).post(f"{REQUESTS_URL}{request_id}/process/")
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_notifications_for(org["requester"]))
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.notification_type == "purchase_request_processed"
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == request_id
        assert response.data["requisition_number"] in notification.message

    def test_retrying_processing_does_not_duplicate_the_notification(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)
        self._advance_to_procurement(login, org, request_id)
        client = login(org["procurement"])

        first = client.post(f"{REQUESTS_URL}{request_id}/process/")
        assert first.status_code == status.HTTP_200_OK
        assert _notifications_for(org["requester"]).count() == 1

        retry = client.post(f"{REQUESTS_URL}{request_id}/process/")
        assert retry.status_code != status.HTTP_200_OK
        assert _notifications_for(org["requester"]).count() == 1

    def test_intermediate_approval_stages_do_not_notify_the_requester(
        self, login, org, payload
    ):
        """
        MVP notification policy: only REJECTED and PROCESSED notify the
        requester - department head/accounts/GM/director approvals must not.
        """
        request_id = create_and_submit(login, org, payload)

        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        assert _notifications_for(org["requester"]).count() == 0

        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")
        assert _notifications_for(org["requester"]).count() == 0

        login(org["gm"]).post(f"{REQUESTS_URL}{request_id}/gm/recommend/")
        assert _notifications_for(org["requester"]).count() == 0

        login(org["director"]).post(f"{REQUESTS_URL}{request_id}/director/approve/")
        assert _notifications_for(org["requester"]).count() == 0

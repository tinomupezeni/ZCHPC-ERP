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


class TestCorrectedAndResubmittedNotification:
    """
    F19: a rejected request, corrected and resubmitted, returns to
    PENDING_DEPARTMENT_HEAD via the normal submit flow - the department
    head must be told this is a correction, not a first-time submission.
    """

    def _reject_correct_and_resubmit(self, login, org, request_id, rejector_key, reason):
        rejected = login(org[rejector_key]).post(
            f"{REQUESTS_URL}{request_id}/reject/", {"reason": reason}, format="json"
        )
        assert rejected.status_code == status.HTTP_200_OK, rejected.data

        client = login(org["requester"])
        corrected = client.post(f"{REQUESTS_URL}{request_id}/correct-and-resubmit/")
        assert corrected.status_code == status.HTTP_200_OK, corrected.data
        assert corrected.data["status"] == "DRAFT"

        resubmitted = client.post(f"{REQUESTS_URL}{request_id}/submit/")
        assert resubmitted.status_code == status.HTTP_200_OK, resubmitted.data
        return resubmitted

    def test_correction_after_department_head_rejection_notifies_the_department_head(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        resubmitted = self._reject_correct_and_resubmit(
            login, org, request_id, "department_head", "Missing detail"
        )

        assert resubmitted.data["status"] == "PENDING_DEPARTMENT_HEAD"
        notifications = list(_notifications_for(org["department_head"]))
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.notification_type == "purchase_request_corrected"
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == request_id
        assert resubmitted.data["requisition_number"] in notification.message
        assert "re-approval" in notification.message.lower()
        assert notification.is_read is False

    def test_correction_after_a_later_stage_rejection_still_notifies_the_department_head(
        self, login, org, payload
    ):
        """
        F19 must not assume only Accounts (or only Department Head) can be
        the rejecting stage - here Accounts rejects, but the resubmission
        still lands back at PENDING_DEPARTMENT_HEAD and still notifies Hana.
        """
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        resubmitted = self._reject_correct_and_resubmit(
            login, org, request_id, "accounts", "Category needs revisiting"
        )

        assert resubmitted.data["status"] == "PENDING_DEPARTMENT_HEAD"
        notifications = list(_notifications_for(org["department_head"]))
        assert len(notifications) == 1
        assert notifications[0].notification_type == "purchase_request_corrected"

    def test_the_requester_is_not_the_one_notified(self, login, org, payload):
        """
        The requester does legitimately get a *rejection* notification from
        the earlier reject step (Slice 3, unrelated to this) - what must be
        false is that the requester also receives the *corrected* one.
        """
        request_id = create_and_submit(login, org, payload)

        self._reject_correct_and_resubmit(
            login, org, request_id, "department_head", "Missing detail"
        )

        assert (
            _notifications_for(org["requester"])
            .filter(notification_type="purchase_request_corrected")
            .count()
            == 0
        )

    def test_previous_decision_history_remains_intact_after_correction(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        resubmitted = self._reject_correct_and_resubmit(
            login, org, request_id, "accounts", "Category needs revisiting"
        )

        decisions = resubmitted.data["decisions"]
        assert len(decisions) == 2
        assert decisions[0]["stage"] == "DEPARTMENT_HEAD"
        assert decisions[0]["decision"] == "APPROVED"
        assert decisions[1]["stage"] == "ACCOUNTS"
        assert decisions[1]["decision"] == "REJECTED"
        assert decisions[1]["reason"] == "Category needs revisiting"

    def test_a_normal_first_time_submission_does_not_produce_a_corrected_notification(
        self, login, org, payload
    ):
        create_and_submit(login, org, payload)

        assert _notifications_for(org["department_head"]).count() == 0

    def test_department_with_no_recorded_head_still_lets_the_resubmission_succeed(
        self, login, org, payload
    ):
        """
        Matches the existing non-strict notification policy: a missing
        recipient must not block or fail an otherwise-successful
        resubmission (see ProcessPurchaseRequestByProcurement's docstring).

        The department head is removed only *after* rejecting (rejecting
        itself requires her to still be the recorded head) and *before* the
        resubmission, so this isolates "no recipient at notification time"
        from "no rejecting authority at rejection time".
        """
        request_id = create_and_submit(login, org, payload)
        rejected = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/", {"reason": "Missing detail"}, format="json"
        )
        assert rejected.status_code == status.HTTP_200_OK, rejected.data

        org["it"].head = None
        org["it"].save(update_fields=["head"])

        client = login(org["requester"])
        corrected = client.post(f"{REQUESTS_URL}{request_id}/correct-and-resubmit/")
        assert corrected.status_code == status.HTTP_200_OK, corrected.data

        resubmitted = client.post(f"{REQUESTS_URL}{request_id}/submit/")

        assert resubmitted.status_code == status.HTTP_200_OK, resubmitted.data
        assert resubmitted.data["status"] == "PENDING_DEPARTMENT_HEAD"
        # The earlier rejection still legitimately notified the requester
        # (Slice 3, unrelated) - only the *corrected* notification is what a
        # missing department head must suppress.
        assert (
            Notification.objects.filter(
                related_object_type="purchase_request",
                related_object_id=request_id,
                notification_type="purchase_request_corrected",
            ).count()
            == 0
        )

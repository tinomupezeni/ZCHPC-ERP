"""
F27 - Reviewer Notification Coverage, end to end.

Runs against the full stack (real HTTP, real login, real event bus, real
DjangoNotificationRepository) - see test_notifications.py's own module
docstring for why this is the only place that actually proves procurement's
published domain events reach modules.portal.event_handlers and land in the
database.

Shared fixtures (org, login, payload, create_and_submit) live in
tests/integration/modules/procurement/e2e/conftest.py; org's "department_head"
/ "accounts" / "gm" / "director" / "procurement" keys are the sole holder of
that stage's capability unless a test adds another one itself.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from modules.hr.infrastructure.persistence.models import Employees, Position, Role
from modules.portal.infrastructure.persistence.models import Notification
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from tests.integration.modules.procurement.e2e.conftest import (
    PASSWORD,
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db


def _notifications_for(employee):
    return Notification.objects.filter(employee_id=employee.id).order_by("-created_at")


def _awaiting_review_notifications_for(employee):
    return _notifications_for(employee).filter(
        notification_type__startswith="purchase_request_awaiting_"
    )


def _second_employee_with_permission(org, name, permission, department_key="it"):
    """A second holder of the same stage capability, to prove fan-out."""
    User = get_user_model()
    role = Role.objects.create(
        name=f"{permission.upper()}_2", permissions=[permission]
    )
    slug = name.lower().replace(" ", ".")
    user = User.objects.create_user(
        email=f"{slug}@zchpc.test",
        password=PASSWORD,
        first_name=name.split()[0],
        last_name=name.split()[-1],
    )
    return Employees.objects.create(
        user=user,
        first_name=name.split()[0],
        surname=name.split()[-1],
        email=f"{slug}.emp@zchpc.test",
        department=org[department_key],
        position=Position.objects.create(title=name),
        role=role,
    )


class TestForwardTransitionsNotifyTheNextStage:
    def test_submit_notifies_the_department_head(self, login, org, payload):
        client = login(org["requester"])
        created = client.post(REQUESTS_URL, payload, format="json")
        request_id = created.data["id"]

        response = client.post(f"{REQUESTS_URL}{request_id}/submit/")
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_notifications_for(org["department_head"]))
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.notification_type == "purchase_request_awaiting_department_head"
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == request_id
        assert response.data["requisition_number"] in notification.message
        # The requester is not notified about their own submission this way.
        assert _awaiting_review_notifications_for(org["requester"]).count() == 0

    def test_department_head_approval_notifies_accounts(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)

        response = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_awaiting_review_notifications_for(org["accounts"]))
        assert len(notifications) == 1
        assert notifications[0].notification_type == "purchase_request_awaiting_accounts"
        assert notifications[0].related_object_id == request_id
        # The approver gets no *new* notification from their own approval -
        # the one they already have is only the earlier "you have a fresh
        # submission" notice from submit(), never an accounts-stage one.
        assert not _awaiting_review_notifications_for(org["department_head"]).filter(
            notification_type="purchase_request_awaiting_accounts"
        ).exists()

    def test_accounts_verification_notifies_gm(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        response = login(org["accounts"]).post(
            f"{REQUESTS_URL}{request_id}/accounts/verify/"
        )
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_awaiting_review_notifications_for(org["gm"]))
        assert len(notifications) == 1
        assert notifications[0].notification_type == "purchase_request_awaiting_gm"
        assert notifications[0].related_object_id == request_id

    def test_gm_recommendation_notifies_director(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")

        response = login(org["gm"]).post(f"{REQUESTS_URL}{request_id}/gm/recommend/")
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_awaiting_review_notifications_for(org["director"]))
        assert len(notifications) == 1
        assert notifications[0].notification_type == "purchase_request_awaiting_director"
        assert notifications[0].related_object_id == request_id

    def test_director_approval_notifies_procurement(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")
        login(org["gm"]).post(f"{REQUESTS_URL}{request_id}/gm/recommend/")

        response = login(org["director"]).post(
            f"{REQUESTS_URL}{request_id}/director/approve/"
        )
        assert response.status_code == status.HTTP_200_OK

        notifications = list(_awaiting_review_notifications_for(org["procurement"]))
        assert len(notifications) == 1
        assert notifications[0].notification_type == "purchase_request_awaiting_procurement"
        assert notifications[0].related_object_id == request_id

    def test_processing_fires_no_further_awaiting_review_notification(
        self, login, org, payload
    ):
        """PROCESSED is a terminal state - there is no next stage to notify."""
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")
        login(org["gm"]).post(f"{REQUESTS_URL}{request_id}/gm/recommend/")
        login(org["director"]).post(f"{REQUESTS_URL}{request_id}/director/approve/")

        before = {
            person: _awaiting_review_notifications_for(org[person]).count()
            for person in ("requester", "department_head", "accounts", "gm", "director", "procurement")
        }

        response = login(org["procurement"]).post(
            f"{REQUESTS_URL}{request_id}/process/",
            {"purchase_order_number": "PO-F27-001"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        # The existing "processed" notification still fires for the requester...
        assert (
            _notifications_for(org["requester"])
            .filter(notification_type="purchase_request_processed")
            .count()
            == 1
        )
        # ...but nobody gets a new awaiting-review notification for it - the
        # count for every role is exactly what it was before processing.
        for person, count_before in before.items():
            assert _awaiting_review_notifications_for(org[person]).count() == count_before


class TestNoCrossRoleNotifications:
    def test_a_holder_of_a_later_stages_permission_is_not_notified_early(
        self, login, org, payload
    ):
        """Submitting must only ever reach the department head, never GM/Director/Procurement/Accounts."""
        client = login(org["requester"])
        created = client.post(REQUESTS_URL, payload, format="json")
        request_id = created.data["id"]

        client.post(f"{REQUESTS_URL}{request_id}/submit/")

        for person in ("accounts", "gm", "director", "procurement"):
            assert _awaiting_review_notifications_for(org[person]).count() == 0

    def test_accounts_holder_never_gets_a_gm_stage_notification(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        login(org["accounts"]).post(f"{REQUESTS_URL}{request_id}/accounts/verify/")

        gm_notifications = _awaiting_review_notifications_for(org["accounts"])
        assert not gm_notifications.filter(
            notification_type="purchase_request_awaiting_gm"
        ).exists()


class TestMultipleHoldersOfTheSamePermission:
    def test_every_current_accounts_holder_is_notified(self, login, org, payload):
        second_accountant = _second_employee_with_permission(
            org, "Anna Accounts", P.ACCOUNTS_VERIFY, department_key="finance"
        )
        request_id = create_and_submit(login, org, payload)

        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        for accountant in (org["accounts"], second_accountant):
            notifications = list(_awaiting_review_notifications_for(accountant))
            assert len(notifications) == 1
            assert notifications[0].related_object_id == request_id


class TestCorrectedResubmissionDoesNotDoubleNotify:
    def test_department_head_gets_only_the_corrected_notification_not_also_awaiting_review(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)
        rejected = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Please pick a different model"},
            format="json",
        )
        assert rejected.status_code == status.HTTP_200_OK
        Notification.objects.filter(employee_id=org["department_head"].id).delete()

        requester_client = login(org["requester"])
        corrected = requester_client.post(
            f"{REQUESTS_URL}{request_id}/correct-and-resubmit/"
        )
        assert corrected.status_code == status.HTTP_200_OK
        resubmitted = requester_client.post(f"{REQUESTS_URL}{request_id}/submit/")
        assert resubmitted.status_code == status.HTTP_200_OK

        head_notifications = _notifications_for(org["department_head"])
        assert head_notifications.count() == 1
        assert head_notifications.first().notification_type == "purchase_request_corrected"
        assert not head_notifications.filter(
            notification_type="purchase_request_awaiting_department_head"
        ).exists()

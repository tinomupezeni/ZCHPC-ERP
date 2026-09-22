"""
Slice 3 - the Purchase Request notification API endpoints, end to end.

These endpoints (list, unread-count, mark-read, mark-all-read) existed before
this slice but were completely broken at runtime: DjangoNotificationRepository
imported a non-existent `employee_portal.models` package, and the
Notification domain entity's own constructor couldn't be called at all (a
plain @dataclass over Entity[int] doesn't accept `id` as a keyword - see
modules/portal/domain/entities/notification.py and
modules/portal/infrastructure/persistence/django_repositories.py). Both are
fixed as part of making Purchase Request notifications functional, and these
tests are what actually exercises that fix over real HTTP + a real database,
rather than only trusting that the import line looks right.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.portal.infrastructure.persistence.models import Notification

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = "/api/v2/portal/notifications/"
User = get_user_model()


@pytest.fixture
def make_employee(db):
    counter = {"n": 0}

    def _make(name="Test Employee"):
        counter["n"] += 1
        slug = f"{name.lower().replace(' ', '.')}.{counter['n']}"
        user = User.objects.create_user(
            email=f"{slug}@example.com",
            password="testpass123",
            first_name=name.split()[0],
            last_name=name.split()[-1],
        )
        # "portal.*" here is only the real production convention (see
        # hr/migrations/0017_seed_role_permissions.py), not a requirement:
        # RBACMiddleware exempts /api/v2/portal/notifications/* from its
        # per-module check entirely (F27 follow-up - notifications are a
        # personal resource, not a module capability), so any authenticated
        # role would reach these endpoints just as well - see
        # tests/integration/modules/identity/test_rbac_route_access.py and
        # test_notification_access.py for that with a realistic, portal-less
        # Purchase Request permission set.
        role = Role.objects.create(
            name=f"STAFF_{counter['n']}",
            display_name="Staff",
            permissions=["portal.*"],
        )
        return Employees.objects.create(
            user=user,
            first_name=name.split()[0],
            surname=name.split()[-1],
            email=f"{slug}.emp@example.com",
            role=role,
        )

    return _make


@pytest.fixture
def client_for():
    def _client(employee):
        client = APIClient()
        token = AccessToken.for_user(employee.user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _client


@pytest.fixture
def employee(make_employee):
    return make_employee("Riley Requester")


@pytest.fixture
def other_employee(make_employee):
    return make_employee("Olu Other")


class TestListNotifications:
    def test_lists_only_the_caller_own_notifications_newest_first(
        self, client_for, employee, other_employee
    ):
        older = Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_rejected",
            title="Purchase Request Rejected",
            message="Your purchase requisition PR-00001 was rejected. Reason: Too costly",
            related_object_type="purchase_request",
            related_object_id=1,
        )
        newer = Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_processed",
            title="Purchase Request Processed",
            message="Your purchase requisition PR-00002 has been processed by Procurement.",
            related_object_type="purchase_request",
            related_object_id=2,
        )
        Notification.objects.create(
            employee=other_employee,
            notification_type="purchase_request_processed",
            title="Purchase Request Processed",
            message="Not yours",
            related_object_type="purchase_request",
            related_object_id=3,
        )

        response = client_for(employee).get(NOTIFICATIONS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert [n["id"] for n in response.data] == [newer.id, older.id]
        assert response.data[0]["related_object_type"] == "purchase_request"
        assert response.data[0]["related_object_id"] == 2
        assert response.data[1]["message"].startswith("Your purchase requisition PR-00001")


class TestUnreadCount:
    def test_counts_only_the_caller_own_unread_notifications(
        self, client_for, employee, other_employee
    ):
        Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )
        Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_processed",
            title="Processed",
            message="msg",
            is_read=True,
        )
        Notification.objects.create(
            employee=other_employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )

        response = client_for(employee).get(f"{NOTIFICATIONS_URL}unread-count/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"unread_count": 1}


class TestMarkNotificationRead:
    def test_marks_the_caller_own_notification_as_read(self, client_for, employee):
        notification = Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )

        response = client_for(employee).patch(
            f"{NOTIFICATIONS_URL}{notification.id}/read/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_cannot_mark_another_employees_notification_as_read(
        self, client_for, employee, other_employee
    ):
        """
        Ownership guard (Slice 3 fix): ids are sequential across every
        employee's notifications, so an id existing at all must not be
        enough to act on it.
        """
        someone_elses = Notification.objects.create(
            employee=other_employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )

        response = client_for(employee).patch(
            f"{NOTIFICATIONS_URL}{someone_elses.id}/read/"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        someone_elses.refresh_from_db()
        assert someone_elses.is_read is False


class TestMarkAllNotificationsRead:
    def test_marks_only_the_caller_own_unread_notifications(
        self, client_for, employee, other_employee
    ):
        mine = Notification.objects.create(
            employee=employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )
        theirs = Notification.objects.create(
            employee=other_employee,
            notification_type="purchase_request_rejected",
            title="Rejected",
            message="msg",
        )

        response = client_for(employee).post(f"{NOTIFICATIONS_URL}mark-all-read/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"marked_read": 1}
        mine.refresh_from_db()
        theirs.refresh_from_db()
        assert mine.is_read is True
        assert theirs.is_read is False

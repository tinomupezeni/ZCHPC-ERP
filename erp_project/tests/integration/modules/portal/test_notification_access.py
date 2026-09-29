"""
F27 follow-up - notification access for every Employee Portal role.

Slice 3's own test_notification_api.py already proves list/unread-count/
mark-read work correctly once a caller is authenticated - but its
`make_employee` fixture always grants "portal.*", which was itself the
undocumented precondition for reaching /api/v2/portal/notifications/* at
all (see RBACMiddleware). That masked the real-world bug: every Purchase
Request actor (employee, accountant, department head, GM, director,
procurement officer) is seeded with only procurement.purchase_request.*
permissions and no portal grant, so all of them got 403 on their own
notifications - RBACMiddleware.test_rbac_route_access.py now pins down the
route-gate mechanics of the fix; this file proves the fix end to end, with
each role's own realistic Purchase Request permission set and real
Notification rows, matching how manual UI testing actually exercised it
(Riley/Employee, Adam/Accounts, Hana/Department Head all denied; only Hana,
who happened to hold a one-off portal permission, was not).
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

import pytest
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.portal.infrastructure.persistence.models import Notification
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = "/api/v2/portal/notifications/"
UNREAD_COUNT_URL = f"{NOTIFICATIONS_URL}unread-count/"
User = get_user_model()


@pytest.fixture
def make_pr_employee(db):
    """
    An employee holding exactly the given Purchase Request permissions and
    nothing portal-related - the realistic shape of every seeded PR actor
    (see seed_pr_test_data.py / tests/integration/modules/procurement's own
    make_employee), which is exactly the shape that used to 403 on
    notifications.
    """
    counter = {"n": 0}

    def _make(name, permissions):
        counter["n"] += 1
        slug = f"{name.lower().replace(' ', '.')}.{counter['n']}"
        user = User.objects.create_user(
            email=f"{slug}@zchpc.test",
            password="testpass123",
            first_name=name.split()[0],
            last_name=name.split()[-1],
        )
        role = Role.objects.create(
            name=f"PR_ROLE_{counter['n']}",
            display_name=name,
            permissions=list(permissions),
        )
        return Employees.objects.create(
            user=user,
            first_name=name.split()[0],
            surname=name.split()[-1],
            email=f"{slug}.emp@zchpc.test",
            role=role,
        )

    return _make


@pytest.fixture
def client_for():
    def _client(employee):
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}"
        )
        return client

    return _client


def _notification_for(employee, *, is_read=False, title="Notice"):
    return Notification.objects.create(
        employee=employee,
        notification_type="purchase_request_awaiting_department_head",
        title=title,
        message="msg",
        is_read=is_read,
        related_object_type="purchase_request",
        related_object_id=1,
    )


ROLES = [
    ("employee", "Riley Requester", [P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT]),
    ("accountant", "Adam Accounts", [P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT]),
    ("department_head", "Hana Head", [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT]),
    ("reviewer_gm", "Gina Manager", [P.GM_RECOMMEND, P.VIEW, P.REJECT]),
    ("reviewer_director", "Dana Director", [P.DIRECTOR_APPROVE, P.VIEW, P.REJECT]),
    ("reviewer_procurement", "Pat Procure", [P.PROCESS, P.VIEW]),
]


class TestEachRoleCanRetrieveItsOwnNotifications:
    @pytest.mark.parametrize("key,name,permissions", ROLES, ids=[r[0] for r in ROLES])
    def test_role_lists_its_own_notification(
        self, make_pr_employee, client_for, key, name, permissions
    ):
        employee = make_pr_employee(name, permissions)
        notification = _notification_for(employee, title=f"For {name}")

        response = client_for(employee).get(NOTIFICATIONS_URL)

        assert response.status_code == status.HTTP_200_OK, response.data
        assert [n["id"] for n in response.data] == [notification.id]
        assert response.data[0]["title"] == f"For {name}"

    @pytest.mark.parametrize("key,name,permissions", ROLES, ids=[r[0] for r in ROLES])
    def test_unread_count_works_for_the_role(
        self, make_pr_employee, client_for, key, name, permissions
    ):
        employee = make_pr_employee(name, permissions)
        _notification_for(employee, is_read=False)
        _notification_for(employee, is_read=True)

        response = client_for(employee).get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data == {"unread_count": 1}

    def test_a_role_with_zero_permissions_anywhere_still_reaches_its_own_notifications(
        self, make_pr_employee, client_for
    ):
        """Requirement #1 is literal: *every* authenticated user, regardless of role."""
        employee = make_pr_employee("Nora Nobody", [])
        _notification_for(employee)

        response = client_for(employee).get(NOTIFICATIONS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


class TestCrossUserIsolationIsPreserved:
    def test_a_role_cannot_list_another_users_notifications(
        self, make_pr_employee, client_for
    ):
        requester = make_pr_employee("Riley Requester", [P.CREATE, P.VIEW])
        accountant = make_pr_employee("Adam Accounts", [P.ACCOUNTS_VERIFY])
        _notification_for(accountant, title="Adam's notification")

        response = client_for(requester).get(NOTIFICATIONS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_unread_count_does_not_leak_across_users(self, make_pr_employee, client_for):
        requester = make_pr_employee("Riley Requester", [P.CREATE, P.VIEW])
        accountant = make_pr_employee("Adam Accounts", [P.ACCOUNTS_VERIFY])
        _notification_for(accountant, is_read=False)
        _notification_for(accountant, is_read=False)

        response = client_for(requester).get(UNREAD_COUNT_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"unread_count": 0}

    def test_two_different_roles_each_see_only_their_own(
        self, make_pr_employee, client_for
    ):
        requester = make_pr_employee("Riley Requester", [P.CREATE, P.VIEW])
        department_head = make_pr_employee(
            "Hana Head", [P.DEPARTMENT_HEAD_APPROVE, P.VIEW]
        )
        mine = _notification_for(requester, title="Riley's")
        theirs = _notification_for(department_head, title="Hana's")

        riley_ids = {n["id"] for n in client_for(requester).get(NOTIFICATIONS_URL).data}
        hana_ids = {
            n["id"] for n in client_for(department_head).get(NOTIFICATIONS_URL).data
        }

        assert riley_ids == {mine.id}
        assert hana_ids == {theirs.id}
        assert riley_ids.isdisjoint(hana_ids)

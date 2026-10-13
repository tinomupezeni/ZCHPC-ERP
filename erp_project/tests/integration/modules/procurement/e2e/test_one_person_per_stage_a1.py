"""
A-1: each approval step of a purchase request is done by a different person.

The supervisor confirmed the rule in writing (Fri 2026-10-09: one person may not
act at two stages of the same PR). Before this, it held only because each
seeded role has one stage capability; ADMIN ("*") could verify, recommend,
approve and process the same request. The policy now refuses anyone who
recorded a decision at another stage of the request, admins included
(ONE_PERSON_PER_STAGE, 403). Acting again at the same stage - a corrected
resubmission back at the same desk - is still allowed.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from modules.hr.infrastructure.persistence.models import Employees, Position, Role
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestDecision,
)
from tests.integration.modules.procurement.e2e.conftest import (
    PASSWORD,
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db

APPROVE_DH = "department-head/approve/"
VERIFY = "accounts/verify/"
RECOMMEND = "gm/recommend/"
APPROVE_DIRECTOR = "director/approve/"
PROCESS = "process/"


def make_employee(name, role_name, permissions, department):
    role, _ = Role.objects.get_or_create(name=role_name, defaults={"display_name": role_name})
    role.permissions = list(permissions)
    role.save(update_fields=["permissions"])
    slug = name.lower().replace(" ", ".")
    user = get_user_model().objects.create_user(email=f"{slug}@zchpc.test", password=PASSWORD)
    return Employees.objects.create(
        user=user,
        first_name=name.split()[0],
        surname=name.split()[-1],
        email=f"{slug}.emp@zchpc.test",
        department=department,
        position=Position.objects.create(title=role_name.title()),
        role=role,
        phone="+263771000222",
    )


@pytest.fixture
def admin(org):
    """A system administrator with every capability and an employee profile."""
    return make_employee("Ada Admin", "ADMIN", ["*"], org["finance"])


def act(login, employee, request_id, path):
    body = {"purchase_order_number": "PO-A1"} if path == PROCESS else None
    return login(employee).post(f"{REQUESTS_URL}{request_id}/{path}", body, format="json")


def assert_refused(response, request_id, still_at):
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
    assert response.data["code"] == "ONE_PERSON_PER_STAGE"
    assert PurchaseRequestModel.objects.get(pk=request_id).status == still_at


class TestAdminCannotActAtTwoStages:
    def test_admin_who_verified_cannot_recommend(self, login, org, payload, admin):
        request_id = create_and_submit(login, org, payload)
        assert act(login, org["department_head"], request_id, APPROVE_DH).status_code == 200
        assert act(login, admin, request_id, VERIFY).status_code == 200

        assert_refused(act(login, admin, request_id, RECOMMEND), request_id, "PENDING_GM")

        # A different person still can.
        assert act(login, org["gm"], request_id, RECOMMEND).status_code == 200

    def test_admin_heading_the_department_cannot_also_verify(self, login, org, payload, admin):
        org["it"].head = admin
        org["it"].save(update_fields=["head"])
        request_id = create_and_submit(login, org, payload)
        assert act(login, admin, request_id, APPROVE_DH).status_code == 200

        assert_refused(act(login, admin, request_id, VERIFY), request_id, "PENDING_ACCOUNTS")

    def test_admin_who_approved_as_director_cannot_process(self, login, org, payload, admin):
        request_id = create_and_submit(login, org, payload)
        for person, path in [("department_head", APPROVE_DH), ("accounts", VERIFY), ("gm", RECOMMEND)]:
            assert act(login, org[person], request_id, path).status_code == 200
        assert act(login, admin, request_id, APPROVE_DIRECTOR).status_code == 200

        assert_refused(act(login, admin, request_id, PROCESS), request_id, "PENDING_PROCUREMENT")

    def test_admin_who_verified_cannot_reject_at_a_later_stage(self, login, org, payload, admin):
        request_id = create_and_submit(login, org, payload)
        assert act(login, org["department_head"], request_id, APPROVE_DH).status_code == 200
        assert act(login, admin, request_id, VERIFY).status_code == 200

        response = login(admin).post(
            f"{REQUESTS_URL}{request_id}/reject/", {"reason": "second stage"}, format="json"
        )
        assert_refused(response, request_id, "PENDING_GM")


class TestAnyMultiCapabilityHolder:
    def test_a_non_admin_holding_two_stage_capabilities_acts_at_only_one(self, login, org, payload):
        both = make_employee(
            "Bo Both", "ACCOUNTS_AND_GM", [P.ACCOUNTS_VERIFY, P.GM_RECOMMEND, P.VIEW], org["finance"]
        )
        request_id = create_and_submit(login, org, payload)
        assert act(login, org["department_head"], request_id, APPROVE_DH).status_code == 200
        assert act(login, both, request_id, VERIFY).status_code == 200

        assert_refused(act(login, both, request_id, RECOMMEND), request_id, "PENDING_GM")


class TestSameStageAgainIsAllowed:
    def test_the_same_head_reviews_a_corrected_resubmission(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        rejected = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/", {"reason": "Add a quote"}, format="json"
        )
        assert rejected.status_code == 200
        requester = login(org["requester"])
        assert requester.post(f"{REQUESTS_URL}{request_id}/correct-and-resubmit/").status_code == 200
        assert requester.post(f"{REQUESTS_URL}{request_id}/submit/").status_code == 200

        approved = act(login, org["department_head"], request_id, APPROVE_DH)

        assert approved.status_code == status.HTTP_200_OK, approved.data
        assert approved.data["status"] == "PENDING_ACCOUNTS"
        assert PurchaseRequestDecision.objects.filter(purchase_request_id=request_id).count() == 2

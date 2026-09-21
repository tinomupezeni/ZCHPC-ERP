"""
Slice 6 - invalid transitions and list/queue semantics.

Shared fixtures (org, login, payload, create_and_submit) live in conftest.py.
"""


import pytest
from rest_framework import status

from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestDecision,
)
from tests.integration.modules.procurement.e2e.conftest import (
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# 5. Invalid workflow transitions are refused by the domain
# =============================================================================


class TestInvalidTransitions:
    @pytest.mark.parametrize(
        "person,path",
        [
            ("department_head", "department-head/approve/"),
            ("accounts", "accounts/verify/"),
            ("gm", "gm/recommend/"),
            ("director", "director/approve/"),
            ("procurement", "process/"),
        ],
    )
    def test_stage_cannot_be_reached_before_its_turn(
        self, login, org, payload, person, path
    ):
        """A DRAFT request cannot jump to any approval stage."""
        client = login(org["requester"])
        created = client.post(REQUESTS_URL, payload, format="json")
        request_id = created.data["id"]

        response = login(org[person]).post(f"{REQUESTS_URL}{request_id}/{path}")

        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        )
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "DRAFT"
        assert PurchaseRequestDecision.objects.count() == 0

    def test_accounts_cannot_verify_before_department_head_approves(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        response = login(org["accounts"]).post(
            f"{REQUESTS_URL}{request_id}/accounts/verify/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert PurchaseRequestDecision.objects.count() == 0

    def test_director_cannot_approve_before_gm_recommends(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        response = login(org["director"]).post(
            f"{REQUESTS_URL}{request_id}/director/approve/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_ACCOUNTS"
        # only the department head decision exists
        assert PurchaseRequestDecision.objects.count() == 1

    def test_procurement_cannot_process_before_director_approves(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        # A well-formed body is supplied so this actually exercises the
        # domain's PENDING_PROCUREMENT status check, not merely
        # ProcessPurchaseRequestInputSerializer's shape validation.
        response = login(org["procurement"]).post(
            f"{REQUESTS_URL}{request_id}/process/",
            {"purchase_order_number": "PO-TOO-EARLY"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert record.processed_by_id is None
        assert record.processed_at is None
        assert record.purchase_order_number is None


# =============================================================================
# 6. List and queue semantics
# =============================================================================


class TestListAndQueueIntegration:
    def test_default_list_returns_only_the_callers_requests(
        self, login, org, payload
    ):
        mine = create_and_submit(login, org, payload)

        # A request raised by somebody else in the same department.
        other_client = login(org["gm"])
        org["gm"].role.permissions = [P.CREATE, P.VIEW, P.SUBMIT]
        org["gm"].role.save(update_fields=["permissions"])
        other = other_client.post(REQUESTS_URL, payload, format="json")
        assert other.status_code == status.HTTP_201_CREATED

        response = login(org["requester"]).get(REQUESTS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [mine]

    def test_department_head_queue_only_shows_headed_departments(
        self, login, org, payload
    ):
        it_request = create_and_submit(login, org, payload)

        response = login(org["department_head"]).get(
            f"{REQUESTS_URL}?scope=pending-department-head"
        )

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [it_request]

    @pytest.mark.parametrize(
        "person,scope",
        [
            ("accounts", "pending-accounts"),
            ("gm", "pending-gm"),
            ("director", "pending-director"),
            ("procurement", "pending-procurement"),
        ],
    )
    def test_each_queue_is_reachable_by_its_own_office(
        self, login, org, person, scope
    ):
        response = login(org[person]).get(f"{REQUESTS_URL}?scope={scope}")

        assert response.status_code == status.HTTP_200_OK

    def test_queue_requires_that_stages_capability(self, login, org):
        response = login(org["requester"]).get(
            f"{REQUESTS_URL}?scope=pending-director"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_view_capability_alone_does_not_expose_the_whole_table(
        self, login, org, payload
    ):
        """The requester holds `view`, but that must not list other people's work."""
        create_and_submit(login, org, payload)
        org["gm"].role.permissions = [P.CREATE, P.VIEW, P.SUBMIT]
        org["gm"].role.save(update_fields=["permissions"])
        login(org["gm"]).post(REQUESTS_URL, payload, format="json")

        response = login(org["requester"]).get(REQUESTS_URL)

        assert PurchaseRequestModel.objects.count() == 2
        assert len(response.data) == 1

    def test_unknown_scope_is_rejected(self, login, org):
        response = login(org["requester"]).get(f"{REQUESTS_URL}?scope=everything")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

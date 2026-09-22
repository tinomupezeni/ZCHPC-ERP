"""
Slice 6 - authorization and actor identity through the integrated stack.

Shared fixtures (org, login, payload, create_and_submit) live in conftest.py.
"""


import pytest
from rest_framework import status
from rest_framework.test import APIClient

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
# 3. Authorization through the integrated stack
# =============================================================================


class TestAuthorizationIntegration:
    def test_unauthenticated_caller_is_rejected_and_changes_nothing(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        response = APIClient().post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert PurchaseRequestDecision.objects.count() == 0

    def test_authenticated_actor_without_the_capability_is_refused(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        response = login(org["outsider"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert PurchaseRequestDecision.objects.count() == 0

    def test_head_of_a_different_department_is_refused(self, login, org, payload):
        """
        The accounts actor heads Finance, so holds department-head authority -
        but not over an IT request.
        """
        request_id = create_and_submit(login, org, payload)
        finance_head = org["accounts"]
        finance_head.role.permissions = [P.DEPARTMENT_HEAD_APPROVE, P.VIEW]
        finance_head.role.save(update_fields=["permissions"])

        response = login(finance_head).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "DEPARTMENT_CONTEXT_DENIED"
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert PurchaseRequestDecision.objects.count() == 0

    def test_correctly_authorized_head_succeeds_and_persists(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        response = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_200_OK
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_ACCOUNTS"
        decision = PurchaseRequestDecision.objects.get(purchase_request_id=request_id)
        assert decision.actor_id == org["department_head"].id


# =============================================================================
# 4. Actor identity cannot come from the client
# =============================================================================


class TestActorIdentityIntegration:
    def test_supplied_approver_id_cannot_grant_authority(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)

        response = login(org["outsider"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/",
            {
                "actor_id": org["department_head"].id,
                "approver_id": org["department_head"].id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert PurchaseRequestDecision.objects.count() == 0

    def test_decision_is_attributed_to_the_token_holder(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)

        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/",
            {"actor_id": 999, "approver_id": 999},
            format="json",
        )

        decision = PurchaseRequestDecision.objects.get(purchase_request_id=request_id)
        assert decision.actor_id == org["department_head"].id

    def test_created_request_belongs_to_the_token_holder(self, login, org, payload):
        response = login(org["requester"]).post(
            REQUESTS_URL,
            {
                **payload,
                "requester_id": org["director"].id,
                "requester_name": "Dana Director",
                "department_id": org["finance"].id,
                "designation": "Director",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        record = PurchaseRequestModel.objects.get(pk=response.data["id"])
        assert record.requester_id == org["requester"].id
        assert record.department_id == org["it"].id
        assert record.designation == "Systems Developer"

"""
Slice 6 - rejection, correction and resubmission.

Shared fixtures (org, login, payload, create_and_submit) live in conftest.py.
"""


import pytest
from rest_framework import status

from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestDecision,
    PurchaseRequestItem,
)
from tests.integration.modules.procurement.e2e.conftest import (
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# 2. Rejection -> correction -> resubmission
# =============================================================================


class TestRejectionCorrectionResubmission:
    def test_rejected_request_can_be_corrected_and_completed(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        rejected = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/reject/",
            {"reason": "Specification is incomplete"},
            format="json",
        )
        assert rejected.status_code == status.HTTP_200_OK
        assert rejected.data["status"] == "REJECTED"

        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "REJECTED"
        rejection = PurchaseRequestDecision.objects.get(purchase_request_id=request_id)
        assert rejection.decision == "REJECTED"
        assert rejection.stage == "DEPARTMENT_HEAD"
        assert rejection.reason == "Specification is incomplete"
        assert rejection.actor_id == org["department_head"].id

        corrected = login(org["requester"]).post(
            f"{REQUESTS_URL}{request_id}/correct-and-resubmit/"
        )
        assert corrected.status_code == status.HTTP_200_OK
        assert corrected.data["status"] == "DRAFT"

        # The rejection survives correction - history is append-only.
        assert (
            PurchaseRequestDecision.objects.filter(
                purchase_request_id=request_id, decision="REJECTED"
            ).count()
            == 1
        )

        resubmitted = login(org["requester"]).post(
            f"{REQUESTS_URL}{request_id}/submit/"
        )
        assert resubmitted.status_code == status.HTTP_200_OK
        assert resubmitted.data["status"] == "PENDING_DEPARTMENT_HEAD"

        approved = login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        assert approved.status_code == status.HTTP_200_OK
        assert approved.data["status"] == "PENDING_ACCOUNTS"

        # Both the rejection and the later approval are on record.
        history = PurchaseRequestDecision.objects.filter(
            purchase_request_id=request_id
        ).order_by("id")
        assert [(d.stage, d.decision) for d in history] == [
            ("DEPARTMENT_HEAD", "REJECTED"),
            ("DEPARTMENT_HEAD", "APPROVED"),
        ]
        assert PurchaseRequestItem.objects.filter(
            purchase_request_id=request_id
        ).count() == 2

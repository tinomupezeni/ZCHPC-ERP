"""
Slice 6 - the complete Purchase Request happy path.

Shared fixtures (org, login, payload, create_and_submit) live in conftest.py.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from modules.procurement.infrastructure.persistence.models import (
    PurchaseOrder,
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestDecision,
    PurchaseRequestItem,
)
from tests.integration.modules.procurement.e2e.conftest import (
    REQUESTS_URL,
    create_and_submit,
)

pytestmark = pytest.mark.django_db


def advance_to_processed(login, org, request_id, po_number="PO-E2E-DEFAULT"):
    """
    Approve a submitted request through every stage up to and including
    Procurement processing (F23: process/ now requires a purchase_order_number
    body, unlike the other no-payload transitions).
    """
    for person, path in [
        ("department_head", "department-head/approve/"),
        ("accounts", "accounts/verify/"),
        ("gm", "gm/recommend/"),
        ("director", "director/approve/"),
    ]:
        login(org[person]).post(f"{REQUESTS_URL}{request_id}/{path}")
    login(org["procurement"]).post(
        f"{REQUESTS_URL}{request_id}/process/",
        {"purchase_order_number": po_number},
        format="json",
    )


# =============================================================================
# 1. Complete happy path
# =============================================================================


class TestCompleteHappyPath:
    def test_full_workflow_through_the_real_stack(self, login, org, payload):
        """Create -> submit -> 4 approvals -> process, all over authenticated HTTP."""
        client = login(org["requester"])

        created = client.post(REQUESTS_URL, payload, format="json")
        assert created.status_code == status.HTTP_201_CREATED, created.data
        request_id = created.data["id"]
        assert created.data["status"] == "DRAFT"

        # Accounts owns the budget code; employees never supply one. Stand-in
        # for the Accounts assignment step (a later F25 slice).
        PurchaseRequestItem.objects.filter(purchase_request_id=request_id).update(
            budget_code=org["budget_code"]
        )

        stages = [
            ("requester", "submit/", "PENDING_DEPARTMENT_HEAD", None),
            ("department_head", "department-head/approve/", "PENDING_ACCOUNTS", None),
            ("accounts", "accounts/verify/", "PENDING_GM", None),
            ("gm", "gm/recommend/", "PENDING_DIRECTOR", None),
            ("director", "director/approve/", "PENDING_PROCUREMENT", None),
            (
                "procurement",
                "process/",
                "PROCESSED",
                {"purchase_order_number": "PO-E2E-HAPPY-PATH"},
            ),
        ]

        for person, path, expected_status, body in stages:
            if body is None:
                response = login(org[person]).post(f"{REQUESTS_URL}{request_id}/{path}")
            else:
                response = login(org[person]).post(
                    f"{REQUESTS_URL}{request_id}/{path}", body, format="json"
                )

            assert response.status_code == status.HTTP_200_OK, (path, response.data)
            assert response.data["status"] == expected_status, path

            # Database agrees with the API at every stage, not just the end.
            record = PurchaseRequestModel.objects.get(pk=request_id)
            assert record.status == expected_status, path

        assert record.purchase_order_number == "PO-E2E-HAPPY-PATH"

    def test_accounts_cannot_verify_while_a_budget_code_is_unassigned(
        self, login, org, payload
    ):
        client = login(org["requester"])
        request_id = client.post(REQUESTS_URL, payload, format="json").data["id"]
        client.post(f"{REQUESTS_URL}{request_id}/submit/")
        login(org["department_head"]).post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )

        response = login(org["accounts"]).post(
            f"{REQUESTS_URL}{request_id}/accounts/verify/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "BUDGET_CODE_NOT_ASSIGNED"
        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_ACCOUNTS"
        assert not record.decisions.filter(stage="ACCOUNTS").exists()

    def test_persisted_request_matches_what_was_submitted(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        advance_to_processed(login, org, request_id, po_number="PO-E2E-SUBMITTED")

        record = PurchaseRequestModel.objects.get(pk=request_id)

        assert record.requester_id == org["requester"].id
        assert record.department_id == org["it"].id
        assert record.designation == "Systems Developer"  # snapshot of position
        assert record.contact == "+263771000111"  # snapshot of contact
        assert record.requisition_number.startswith("PR-")
        assert record.status == "PROCESSED"
        # payload: 2 x $3000.00 laptop + 2 x $450.50 docking station
        assert record.total_estimated_cost == Decimal("6901.00")
        assert record.created_at is not None
        assert record.updated_at is not None
        assert record.purchase_order_number == "PO-E2E-SUBMITTED"

    def test_all_items_are_persisted_with_their_budget_code(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)

        items = PurchaseRequestItem.objects.filter(
            purchase_request_id=request_id
        ).order_by("id")

        assert items.count() == 2
        laptop, dock = items
        assert laptop.description == "Dell Latitude 5540 laptop"
        assert laptop.quantity == 2
        assert laptop.expected_delivery_period == "3 weeks"
        assert laptop.estimated_cost == Decimal("3000.00")
        assert laptop.category_id == org["category"].id
        assert laptop.budget_code_id == org["budget_code"].id
        assert dock.description == "Docking stations"
        assert dock.estimated_cost == Decimal("450.50")
        assert dock.category_id == org["category"].id
        assert dock.budget_code_id == org["budget_code"].id

    def test_decision_history_records_every_approving_stage(
        self, login, org, payload
    ):
        request_id = create_and_submit(login, org, payload)
        advance_to_processed(login, org, request_id, po_number="PO-E2E-DECISIONS")

        decisions = PurchaseRequestDecision.objects.filter(
            purchase_request_id=request_id
        ).order_by("id")

        assert [(d.stage, d.decision) for d in decisions] == [
            ("DEPARTMENT_HEAD", "APPROVED"),
            ("ACCOUNTS", "VERIFIED"),
            ("GM", "RECOMMENDED"),
            ("DIRECTOR", "APPROVED"),
        ]
        assert [d.actor_id for d in decisions] == [
            org["department_head"].id,
            org["accounts"].id,
            org["gm"].id,
            org["director"].id,
        ]
        assert all(d.created_at is not None for d in decisions)
        assert all(d.reason == "" for d in decisions)

    def test_processing_records_the_procurement_actor(self, login, org, payload):
        request_id = create_and_submit(login, org, payload)
        advance_to_processed(login, org, request_id, po_number="PO-E2E-ACTOR")

        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.processed_by_id == org["procurement"].id
        assert record.processed_at is not None
        assert record.purchase_order_number == "PO-E2E-ACTOR"

    def test_director_approval_does_not_create_a_purchase_order(
        self, login, org, payload
    ):
        """Director approval and procurement processing stay separate."""
        request_id = create_and_submit(login, org, payload)
        for person, path in [
            ("department_head", "department-head/approve/"),
            ("accounts", "accounts/verify/"),
            ("gm", "gm/recommend/"),
        ]:
            login(org[person]).post(f"{REQUESTS_URL}{request_id}/{path}")

        response = login(org["director"]).post(
            f"{REQUESTS_URL}{request_id}/director/approve/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PENDING_PROCUREMENT"
        assert PurchaseOrder.objects.count() == 0

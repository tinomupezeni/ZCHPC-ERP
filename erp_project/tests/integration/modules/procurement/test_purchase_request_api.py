"""
HTTP-boundary tests for the Purchase Request API.

These verify what the API layer is responsible for: authentication, that the
acting employee comes from the token rather than the payload, that each route
invokes the right use case, and that failures map to honest status codes.

Domain state-transition rules are covered by the Slice 2 suite and are not
repeated here.
"""

from unittest.mock import patch

from rest_framework import status

import pytest

from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestItem as PurchaseRequestItemModel,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# Authentication
# =============================================================================


class TestAuthentication:
    def test_anonymous_list_is_rejected(self, anonymous_client, api_url):
        assert anonymous_client.get(api_url).status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_create_is_rejected(self, anonymous_client, api_url, valid_payload):
        response = anonymous_client.post(api_url, valid_payload, format="json")

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        assert PurchaseRequestModel.objects.count() == 0

    def test_anonymous_workflow_action_is_rejected(
        self, anonymous_client, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = anonymous_client.post(
            f"{api_url}{record.id}/department-head/approve/"
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"

    def test_authenticated_request_resolves_the_calling_employee(
        self, client_for, api_url, requester, valid_payload
    ):
        response = client_for(requester).post(api_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["requester_id"] == requester.id
        assert response.data["requester_name"] == "Riley Requester"
        assert response.data["department_id"] == requester.department_id


# =============================================================================
# Actor identity cannot be supplied by the client
# =============================================================================


class TestClientCannotSupplyActorIdentity:
    def test_create_ignores_client_supplied_requester_id(
        self, client_for, api_url, requester, department_head, valid_payload
    ):
        """A forged requester_id must not change who the request belongs to."""
        payload = {
            **valid_payload,
            "requester_id": department_head.id,
            "requester_name": "Hana Head",
            "department_id": 9999,
        }

        response = client_for(requester).post(api_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["requester_id"] == requester.id
        assert response.data["department_id"] == requester.department_id

        record = PurchaseRequestModel.objects.get(pk=response.data["id"])
        assert record.requester_id == requester.id

    def test_approval_ignores_client_supplied_approver_id(
        self,
        client_for,
        api_url,
        requester,
        department_head,
        outsider,
        make_request_record,
    ):
        """
        The legacy API took approver_id from the body. An outsider supplying
        the real head's id must still be refused, and nothing may change.
        """
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(outsider).post(
            f"{api_url}{record.id}/department-head/approve/",
            {"approver_id": department_head.id, "actor_id": department_head.id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"
        assert record.decisions.count() == 0

    def test_decision_is_attributed_to_the_authenticated_employee(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/department-head/approve/",
            {"approver_id": requester.id},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        decision = record.decisions.get()
        assert decision.actor_id == department_head.id


# =============================================================================
# Create / retrieve / list
# =============================================================================


class TestCreateRetrieveList:
    def test_create_persists_the_request_and_items(
        self, client_for, api_url, requester, valid_payload
    ):
        response = client_for(requester).post(api_url, valid_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["status"] == "DRAFT"
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["description"] == "Laptop"
        assert response.data["requisition_number"].startswith("PR-")

    def test_retrieve_returns_the_request(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester)

        response = client_for(requester).get(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == record.id
        assert response.data["status"] == "DRAFT"

    def test_retrieve_requires_the_view_capability(
        self, client_for, api_url, requester, outsider, make_request_record
    ):
        record = make_request_record(requester)

        response = client_for(outsider).get(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_defaults_to_the_callers_own_requests(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        mine = make_request_record(requester)
        make_request_record(department_head)

        response = client_for(requester).get(api_url)

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [mine.id]

    def test_department_head_queue_is_limited_to_headed_departments(
        self,
        client_for,
        api_url,
        requester,
        department_head,
        other_department_head,
        make_request_record,
    ):
        it_request = make_request_record(
            requester, status="PENDING_DEPARTMENT_HEAD", department="it"
        )
        make_request_record(
            other_department_head,
            status="PENDING_DEPARTMENT_HEAD",
            department="finance",
        )

        response = client_for(department_head).get(
            f"{api_url}?scope=pending-department-head"
        )

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [it_request.id]

    def test_queue_requires_that_stages_capability(
        self, client_for, api_url, requester, make_request_record
    ):
        make_request_record(requester, status="PENDING_ACCOUNTS")

        response = client_for(requester).get(f"{api_url}?scope=pending-accounts")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unknown_scope_is_rejected(self, client_for, api_url, requester):
        response = client_for(requester).get(f"{api_url}?scope=everything")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Workflow
# =============================================================================


class TestWorkflow:
    def test_full_happy_path_through_every_stage(
        self,
        client_for,
        api_url,
        requester,
        department_head,
        accountant,
        general_manager,
        director,
        procurement_officer,
        make_request_record,
    ):
        record = make_request_record(requester)
        rid = record.id

        steps = [
            (requester, "submit/", "PENDING_DEPARTMENT_HEAD", None),
            (department_head, "department-head/approve/", "PENDING_ACCOUNTS", None),
            (accountant, "accounts/verify/", "PENDING_GM", None),
            (general_manager, "gm/recommend/", "PENDING_DIRECTOR", None),
            (director, "director/approve/", "PENDING_PROCUREMENT", None),
            (
                procurement_officer,
                "process/",
                "PROCESSED",
                {"purchase_order_number": "PO-2026-00042"},
            ),
        ]

        for actor, path, expected, payload in steps:
            if payload is None:
                response = client_for(actor).post(f"{api_url}{rid}/{path}")
            else:
                response = client_for(actor).post(
                    f"{api_url}{rid}/{path}", payload, format="json"
                )
            assert response.status_code == status.HTTP_200_OK, (path, response.data)
            assert response.data["status"] == expected, path

        assert response.data["purchase_order_number"] == "PO-2026-00042"

        record.refresh_from_db()
        assert record.status == "PROCESSED"
        assert record.processed_by_id == procurement_officer.id
        assert record.purchase_order_number == "PO-2026-00042"

    def test_director_approval_does_not_create_a_purchase_order(
        self, client_for, api_url, requester, director, make_request_record
    ):
        from modules.procurement.infrastructure.persistence.models import PurchaseOrder

        record = make_request_record(requester, status="PENDING_DIRECTOR")

        response = client_for(director).post(f"{api_url}{record.id}/director/approve/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PENDING_PROCUREMENT"
        assert PurchaseOrder.objects.count() == 0

    def test_reject_records_the_reason(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/reject/", {"reason": "Too costly"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REJECTED"
        assert record.decisions.get().reason == "Too costly"

    def test_correct_and_resubmit_returns_a_rejected_request_to_draft(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="REJECTED")

        response = client_for(requester).post(
            f"{api_url}{record.id}/correct-and-resubmit/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "DRAFT"


# =============================================================================
# Procurement processing - PO number (F23)
# =============================================================================


class TestProcurementProcessing:
    def test_process_persists_the_purchase_order_number(
        self, client_for, api_url, requester, procurement_officer, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_PROCUREMENT")

        response = client_for(procurement_officer).post(
            f"{api_url}{record.id}/process/",
            {"purchase_order_number": "PO-2026-777"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "PROCESSED"
        assert response.data["purchase_order_number"] == "PO-2026-777"
        record.refresh_from_db()
        assert record.purchase_order_number == "PO-2026-777"
        assert record.processed_by_id == procurement_officer.id

    def test_process_without_a_purchase_order_number_is_rejected(
        self, client_for, api_url, requester, procurement_officer, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_PROCUREMENT")

        response = client_for(procurement_officer).post(
            f"{api_url}{record.id}/process/", {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.status == "PENDING_PROCUREMENT"
        assert record.purchase_order_number is None

    def test_process_with_a_blank_purchase_order_number_is_rejected(
        self, client_for, api_url, requester, procurement_officer, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_PROCUREMENT")

        response = client_for(procurement_officer).post(
            f"{api_url}{record.id}/process/",
            {"purchase_order_number": "   "},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.status == "PENDING_PROCUREMENT"

    def test_process_with_a_duplicate_purchase_order_number_is_rejected(
        self,
        client_for,
        api_url,
        requester,
        procurement_officer,
        make_request_record,
    ):
        already_processed = make_request_record(requester, status="PENDING_PROCUREMENT")
        already_processed.purchase_order_number = "PO-DUP-1"
        already_processed.save(update_fields=["purchase_order_number"])

        record = make_request_record(requester, status="PENDING_PROCUREMENT")

        response = client_for(procurement_officer).post(
            f"{api_url}{record.id}/process/",
            {"purchase_order_number": "PO-DUP-1"},
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "PO_NUMBER_ALREADY_EXISTS"
        record.refresh_from_db()
        assert record.status == "PENDING_PROCUREMENT"
        assert record.purchase_order_number is None


# =============================================================================
# Edit (Slice 2) - PATCH .../requests/{id}/
# =============================================================================


class TestUpdatePurchaseRequestItems:
    def _payload(self, category_id, **overrides):
        item = {
            "description": "Updated item",
            "quantity": 2,
            "expected_delivery_period": "3 weeks",
            "estimated_cost": "75.00",
            "category_id": category_id,
        }
        item.update(overrides)
        return {"items": [item]}

    def test_requester_can_edit_own_draft(
        self, client_for, api_url, requester, category, budget_code, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            self._payload(category.id, id=record.items.first().id),
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == "DRAFT"
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["description"] == "Updated item"
        assert response.data["items"][0]["category_id"] == category.id
        # An employee edit never touches the Accounts budget code (the
        # requester is not shown it, so check the stored value directly).
        assert "budget_code_id" not in response.data["items"][0]
        assert record.items.get().budget_code_id == budget_code.id

    def test_response_includes_the_resolved_category(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.data["items"][0]["category"] == {
            "id": category.id,
            "name": category.name,
            "is_active": True,
        }

    def test_item_keeps_reporting_its_category_after_the_category_is_deactivated(
        self, client_for, api_url, requester, category, make_request_record
    ):
        """The category is persisted, so it is never lost - only flagged inactive."""
        record = make_request_record(requester, status="DRAFT")
        category.is_active = False
        category.save(update_fields=["is_active"])

        response = client_for(requester).get(f"{api_url}{record.id}/")

        item = response.data["items"][0]
        assert item["category_id"] == category.id
        assert item["category"] == {
            "id": category.id,
            "name": category.name,
            "is_active": False,
        }

    def test_item_without_a_budget_code_serializes_it_as_null(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")
        record.items.update(budget_code=None)

        response = client_for(requester).get(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_200_OK, response.data
        # Requesters never receive budget-code keys - not even as null, which
        # would read as "unassigned".
        assert "budget_code_id" not in response.data["items"][0]
        assert "budget_code" not in response.data["items"][0]
        assert response.data["items"][0]["category_id"] == category.id

    def test_editing_a_rejected_request_returns_it_to_draft(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="REJECTED")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == "DRAFT"

    def test_editing_a_rejected_request_preserves_the_rejection_history(
        self,
        client_for,
        api_url,
        requester,
        department_head,
        category,
        make_request_record,
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")
        client_for(department_head).post(
            f"{api_url}{record.id}/reject/",
            {"reason": "Wrong budget"},
            format="json",
        )

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == "DRAFT"
        reasons = [d["reason"] for d in response.data["decisions"]]
        assert "Wrong budget" in reasons

    def test_updating_an_existing_item_by_id(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")
        existing_item_id = record.items.first().id

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            self._payload(category.id, id=existing_item_id, description="Renamed"),
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["id"] == existing_item_id
        assert response.data["items"][0]["description"] == "Renamed"

    def test_omitting_an_existing_item_removes_it(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            self._payload(category.id, description="Replacement"),
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert len(response.data["items"]) == 1
        assert response.data["items"][0]["description"] == "Replacement"
        assert (
            PurchaseRequestItemModel.objects.filter(purchase_request_id=record.id).count()
            == 1
        )

    def test_adding_a_new_item_alongside_an_existing_one(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")
        existing_item_id = record.items.first().id

        payload = {
            "items": [
                {
                    "id": existing_item_id,
                    "description": "Laptop",
                    "quantity": 1,
                    "expected_delivery_period": "2 weeks",
                    "estimated_cost": "1500.00",
                    "category_id": category.id,
                },
                {
                    "description": "Mouse",
                    "quantity": 2,
                    "expected_delivery_period": "1 week",
                    "estimated_cost": "20.00",
                    "category_id": category.id,
                },
            ]
        }

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", payload, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert len(response.data["items"]) == 2

    def test_unknown_category_is_400(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", self._payload(999999), format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "CATEGORY_NOT_FOUND"

    def test_inactive_category_is_400(
        self, client_for, api_url, requester, inactive_category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            self._payload(inactive_category.id),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "CATEGORY_INACTIVE"

    def test_item_id_belonging_to_another_request_is_400(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")
        other_record = make_request_record(requester, status="DRAFT")
        other_item_id = other_record.items.first().id

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            self._payload(category.id, id=other_item_id),
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "ITEM_NOT_FOUND"

    def test_duplicate_item_id_is_400(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")
        existing_item_id = record.items.first().id
        item = {
            "id": existing_item_id,
            "description": "X",
            "quantity": 1,
            "expected_delivery_period": "1 week",
            "estimated_cost": "10.00",
            "category_id": category.id,
        }

        response = client_for(requester).patch(
            f"{api_url}{record.id}/",
            {"items": [item, {**item, "description": "Y"}]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "DUPLICATE_ITEM_ID"

    def test_editing_a_pending_request_is_400_and_leaves_it_unchanged(
        self, client_for, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_ACCOUNTS")
        original_description = record.items.first().description

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("code") == "REQUEST_NOT_EDITABLE"
        record.refresh_from_db()
        assert record.status == "PENDING_ACCOUNTS"
        assert record.items.first().description == original_description

    def test_another_employee_cannot_edit_someone_elses_draft(
        self, client_for, api_url, requester, outsider, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(outsider).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == "DRAFT"

    def test_editing_a_rejected_request_requires_correct_and_resubmit_permissions(
        self, client_for, api_url, make_employee, category, make_request_record
    ):
        """CREATE alone (no CORRECT/RESUBMIT) is enough for a DRAFT edit, but
        not for a REJECTED one - see authorize_edit."""
        limited = make_employee("Larry Limited", [P.CREATE, P.VIEW, P.SUBMIT])
        record = make_request_record(limited, status="REJECTED")

        response = client_for(limited).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == "REJECTED"

    def test_the_same_limited_actor_can_still_edit_their_own_draft(
        self, client_for, api_url, make_employee, category, make_request_record
    ):
        """Confirms the previous test's denial is REJECTED-specific, not a
        blanket lack of edit capability."""
        limited = make_employee("Larry Limited", [P.CREATE, P.VIEW, P.SUBMIT])
        record = make_request_record(limited, status="DRAFT")

        response = client_for(limited).patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data

    def test_budget_code_id_is_not_an_accepted_field_on_this_endpoint(
        self, client_for, api_url, requester, budget_code, make_request_record
    ):
        """
        The edit endpoint has no budget_code_id field at all - category_id is
        the only path. Supplying budget_code_id instead of category_id must
        not succeed via a back-door direct-GL path; it's simply not a
        declared field, so this fails as a missing category_id.
        """
        record = make_request_record(requester, status="DRAFT")
        payload = {
            "items": [
                {
                    "description": "X",
                    "quantity": 1,
                    "expected_delivery_period": "1 week",
                    "estimated_cost": "10.00",
                    "budget_code_id": budget_code.id,
                }
            ]
        }

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.items.first().budget_code_id == budget_code.id  # unchanged

    def test_invalid_item_leaves_the_original_items_completely_unchanged(
        self, client_for, api_url, requester, category, make_request_record
    ):
        """The atomicity guarantee at the HTTP boundary: nothing is written
        when any item in the batch fails validation."""
        record = make_request_record(requester, status="DRAFT")
        existing_item_id = record.items.first().id
        original_description = record.items.first().description

        payload = {
            "items": [
                {
                    "id": existing_item_id,
                    "description": "Should not persist",
                    "quantity": 1,
                    "expected_delivery_period": "1 week",
                    "estimated_cost": "10.00",
                    "category_id": category.id,
                },
                {
                    "description": "Bad item",
                    "quantity": 1,
                    "expected_delivery_period": "1 week",
                    "estimated_cost": "10.00",
                    "category_id": 999999,
                },
            ]
        }

        response = client_for(requester).patch(
            f"{api_url}{record.id}/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.items.count() == 1
        assert record.items.first().description == original_description

    def test_anonymous_edit_is_rejected(
        self, anonymous_client, api_url, requester, category, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = anonymous_client.patch(
            f"{api_url}{record.id}/", self._payload(category.id), format="json"
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        record.refresh_from_db()
        assert record.status == "DRAFT"


# =============================================================================
# Delete Draft (Slice 4)
# =============================================================================


class TestDeletePurchaseRequest:
    def test_requester_can_delete_own_clean_draft(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(requester).delete(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PurchaseRequestModel.objects.filter(pk=record.id).exists()

    def test_non_requester_cannot_delete_someone_elses_draft(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = client_for(department_head).delete(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert PurchaseRequestModel.objects.filter(pk=record.id).exists()

    def test_non_draft_request_cannot_be_deleted(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(requester).delete(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "NOT_DELETABLE"
        assert PurchaseRequestModel.objects.filter(pk=record.id).exists()

    def test_draft_with_decision_history_cannot_be_deleted(
        self,
        client_for,
        api_url,
        requester,
        department_head,
        category,
        make_request_record,
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")
        client_for(department_head).post(
            f"{api_url}{record.id}/reject/",
            {"reason": "Wrong budget"},
            format="json",
        )
        corrected = client_for(requester).patch(
            f"{api_url}{record.id}/",
            {
                "items": [
                    {
                        "description": "Corrected item",
                        "quantity": 1,
                        "expected_delivery_period": "2 weeks",
                        "estimated_cost": "100.00",
                        "category_id": category.id,
                    }
                ]
            },
            format="json",
        )
        assert corrected.data["status"] == "DRAFT", corrected.data

        response = client_for(requester).delete(f"{api_url}{record.id}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "HAS_DECISION_HISTORY"
        assert PurchaseRequestModel.objects.filter(pk=record.id).exists()

    def test_missing_request_returns_404(self, client_for, api_url, requester):
        response = client_for(requester).delete(f"{api_url}999999/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_delete_is_rejected(
        self, anonymous_client, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="DRAFT")

        response = anonymous_client.delete(f"{api_url}{record.id}/")

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
        assert PurchaseRequestModel.objects.filter(pk=record.id).exists()


# =============================================================================
# Authorization is enforced by Slice 4, surfaced as 403
# =============================================================================


class TestAuthorization:
    @pytest.mark.parametrize(
        "path,record_status,payload",
        [
            ("submit/", "DRAFT", None),
            ("department-head/approve/", "PENDING_DEPARTMENT_HEAD", None),
            ("accounts/verify/", "PENDING_ACCOUNTS", None),
            ("gm/recommend/", "PENDING_GM", None),
            ("director/approve/", "PENDING_DIRECTOR", None),
            # A well-formed body is supplied so this actually exercises
            # authorization (403) rather than shape validation (400) -
            # ProcessPurchaseRequestInputSerializer runs before
            # authorize_processing, same ordering as reject's own serializer.
            ("process/", "PENDING_PROCUREMENT", {"purchase_order_number": "PO-AUTHZ-1"}),
            ("correct-and-resubmit/", "REJECTED", None),
        ],
    )
    def test_actor_without_capability_gets_403_and_nothing_changes(
        self, client_for, api_url, requester, outsider, make_request_record,
        path, record_status, payload,
    ):
        record = make_request_record(requester, status=record_status)

        if payload is None:
            response = client_for(outsider).post(f"{api_url}{record.id}/{path}")
        else:
            response = client_for(outsider).post(
                f"{api_url}{record.id}/{path}", payload, format="json"
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == record_status
        assert record.purchase_order_number is None

    def test_head_of_another_department_is_refused(
        self,
        client_for,
        api_url,
        requester,
        other_department_head,
        make_request_record,
    ):
        """Business-context authorization survives the HTTP boundary."""
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(other_department_head).post(
            f"{api_url}{record.id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"

    def test_requester_cannot_approve_their_own_request(
        self, client_for, api_url, department_head, make_request_record
    ):
        """Self-approval stays denied even for the department's own head."""
        record = make_request_record(department_head, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "SELF_APPROVAL_FORBIDDEN"

    def test_another_employee_cannot_submit_someone_elses_request(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester)

        response = client_for(department_head).post(f"{api_url}{record.id}/submit/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# Missing resources, invalid input, domain failures
# =============================================================================


class TestErrorMapping:
    def test_missing_request_is_404(self, client_for, api_url, requester):
        assert (
            client_for(requester).get(f"{api_url}999999/").status_code
            == status.HTTP_404_NOT_FOUND
        )

    def test_missing_request_on_workflow_action_is_404(
        self, client_for, api_url, department_head
    ):
        response = client_for(department_head).post(
            f"{api_url}999999/department-head/approve/"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_malformed_id_is_not_routed(self, client_for, api_url, requester):
        """
        An id that matches no URL pattern never reaches a view. The route gate
        fails closed on anything it cannot resolve, so this is refused rather
        than routed - either way, no handler runs.
        """
        assert client_for(requester).get(
            f"{api_url}not-a-number/"
        ).status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    @pytest.mark.parametrize(
        "items",
        [
            [{"description": "", "quantity": 1, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "category_id": 1}],
            [{"description": "Laptop", "quantity": 0, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "category_id": 1}],
            [{"description": "Laptop", "quantity": "many",
              "expected_delivery_period": "2w", "estimated_cost": "10.00",
              "category_id": 1}],
            [{"quantity": 1, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "category_id": 1}],
        ],
    )
    def test_malformed_items_are_400(self, client_for, api_url, requester, items):
        response = client_for(requester).post(api_url, {"items": items}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert PurchaseRequestModel.objects.count() == 0

    def test_employee_without_a_position_cannot_raise_a_request(
        self, client_for, api_url, employee_without_position, valid_payload
    ):
        """
        designation is a snapshot of the employee's position and the aggregate
        requires it, so an employee with no position recorded is refused with a
        real error rather than a fabricated designation.
        """
        response = client_for(employee_without_position).post(
            api_url, valid_payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert PurchaseRequestModel.objects.count() == 0

    def test_reject_without_a_reason_is_400(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/reject/", {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"

    def test_invalid_domain_transition_is_400_not_a_false_success(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        """An authorized actor still cannot force an illegal transition."""
        record = make_request_record(requester, status="PROCESSED")

        response = client_for(department_head).post(
            f"{api_url}{record.id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        record.refresh_from_db()
        assert record.status == "PROCESSED"

    def test_submitting_an_itemless_request_is_400(
        self, client_for, api_url, requester, departments
    ):
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequest as PRModel,
        )

        empty = PRModel.objects.create(
            requester=requester,
            department=departments["it"],
            designation="Developer",
            contact="ext 123",
            status="DRAFT",
        )

        response = client_for(requester).post(f"{api_url}{empty.id}/submit/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        empty.refresh_from_db()
        assert empty.status == "DRAFT"


# =============================================================================
# Boundary: the view delegates to the application layer
# =============================================================================


class TestApplicationBoundary:
    def test_approval_route_invokes_the_department_head_use_case(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        target = (
            "modules.procurement.api.purchase_request_views"
            ".ApprovePurchaseRequestByDepartmentHead"
        )
        with patch(target) as use_case_cls:
            use_case_cls.return_value.execute.return_value = None
            client_for(department_head).post(
                f"{api_url}{record.id}/department-head/approve/"
            )

        use_case_cls.return_value.execute.assert_called_once()
        called_id, called_actor = use_case_cls.return_value.execute.call_args.args
        assert called_id == record.id
        assert called_actor.employee_id == department_head.id
        assert called_actor.is_authenticated is True

    def test_reject_route_passes_validated_reason_and_actor(
        self, client_for, api_url, requester, department_head, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_DEPARTMENT_HEAD")

        target = (
            "modules.procurement.api.purchase_request_views.RejectPurchaseRequest"
        )
        with patch(target) as use_case_cls:
            use_case_cls.return_value.execute.return_value = None
            client_for(department_head).post(
                f"{api_url}{record.id}/reject/",
                {"reason": "Out of budget"},
                format="json",
            )

        call = use_case_cls.return_value.execute.call_args
        assert call.args[0] == record.id
        assert call.args[1].employee_id == department_head.id
        assert call.kwargs["reason"] == "Out of budget"

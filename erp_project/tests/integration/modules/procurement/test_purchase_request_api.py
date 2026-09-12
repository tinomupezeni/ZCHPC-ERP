"""
HTTP-boundary tests for the Purchase Request API.

These verify what the API layer is responsible for: authentication, that the
acting employee comes from the token rather than the payload, that each route
invokes the right use case, and that failures map to honest status codes.

Domain state-transition rules are covered by the Slice 2 suite and are not
repeated here.
"""

from unittest.mock import patch

import pytest
from rest_framework import status

from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("without_legacy_url_gates")]


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
            (requester, "submit/", "PENDING_DEPARTMENT_HEAD"),
            (department_head, "department-head/approve/", "PENDING_ACCOUNTS"),
            (accountant, "accounts/verify/", "PENDING_GM"),
            (general_manager, "gm/recommend/", "PENDING_DIRECTOR"),
            (director, "director/approve/", "PENDING_PROCUREMENT"),
            (procurement_officer, "process/", "PROCESSED"),
        ]

        for actor, path, expected in steps:
            response = client_for(actor).post(f"{api_url}{rid}/{path}")
            assert response.status_code == status.HTTP_200_OK, (path, response.data)
            assert response.data["status"] == expected, path

        record.refresh_from_db()
        assert record.status == "PROCESSED"
        assert record.processed_by_id == procurement_officer.id

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
# Authorization is enforced by Slice 4, surfaced as 403
# =============================================================================


class TestAuthorization:
    @pytest.mark.parametrize(
        "path,record_status",
        [
            ("submit/", "DRAFT"),
            ("department-head/approve/", "PENDING_DEPARTMENT_HEAD"),
            ("accounts/verify/", "PENDING_ACCOUNTS"),
            ("gm/recommend/", "PENDING_GM"),
            ("director/approve/", "PENDING_DIRECTOR"),
            ("process/", "PENDING_PROCUREMENT"),
            ("correct-and-resubmit/", "REJECTED"),
        ],
    )
    def test_actor_without_capability_gets_403_and_nothing_changes(
        self, client_for, api_url, requester, outsider, make_request_record,
        path, record_status,
    ):
        record = make_request_record(requester, status=record_status)

        response = client_for(outsider).post(f"{api_url}{record.id}/{path}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        record.refresh_from_db()
        assert record.status == record_status

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
        assert (
            client_for(requester).get(f"{api_url}not-a-number/").status_code
            == status.HTTP_404_NOT_FOUND
        )

    @pytest.mark.parametrize(
        "items",
        [
            [{"description": "", "quantity": 1, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "budget_code_id": 1}],
            [{"description": "Laptop", "quantity": 0, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "budget_code_id": 1}],
            [{"description": "Laptop", "quantity": "many",
              "expected_delivery_period": "2w", "estimated_cost": "10.00",
              "budget_code_id": 1}],
            [{"quantity": 1, "expected_delivery_period": "2w",
              "estimated_cost": "10.00", "budget_code_id": 1}],
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

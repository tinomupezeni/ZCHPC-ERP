"""
F25 Slice 2 - Accounts assigns budget codes per item.

    - GET /api/v2/procurement/budget-codes/
    - PUT /api/v2/procurement/requests/<id>/items/<item_id>/budget-code/

Uses the shared conftest fixtures (accountant, requester, department_head,
make_request_record, client_for, ...).
"""

from decimal import Decimal

import pytest
from rest_framework import status

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestItem as PurchaseRequestItemModel,
)

BUDGET_CODES_URL = "/api/v2/procurement/budget-codes/"


def _account(code, external_type, account_type="regular"):
    return AccountChart.objects.create(
        code=code,
        name=f"Account {code}",
        account_type=account_type,
        external_account_type=external_type,
    )


@pytest.fixture
def chart(db):
    """One account per approved type, plus decoys that must never be offered."""
    return {
        "revenue": _account("R-1", "Revenue"),
        "income": _account("I-1", "Other Income"),
        "expense": _account("E-1", "Other Expense"),
        # `account_type` is a different, structural field: a 'view' account
        # whose external type is approved is still assignable...
        "view_but_approved": _account("E-2", "Other Expense", account_type="view"),
        # ...and a 'regular' account whose external type is not approved is not.
        "cash": _account("C-1", "Cash and Cash Equivalents"),
        "inventory": _account("INV-1", "Inventories"),
        "blank": _account("B-1", ""),
    }


APPROVED = {"R-1", "I-1", "E-1", "E-2"}


def _url(api_url, record, item):
    return f"{api_url}{record.id}/items/{item.id}/budget-code/"


@pytest.fixture
def pending_accounts_record(requester, make_request_record):
    """A PENDING_ACCOUNTS request whose single item has no budget code yet."""
    record = make_request_record(requester, status="PENDING_ACCOUNTS")
    record.items.update(budget_code=None)
    return record


def _second_item(record, category):
    return PurchaseRequestItemModel.objects.create(
        purchase_request=record,
        description="Monitor",
        quantity=2,
        expected_delivery_period="2 weeks",
        estimated_cost=Decimal("300.00"),
        category=category,
        budget_code=None,
    )


class TestListAssignableBudgetCodes:
    def test_only_the_three_approved_external_types_are_offered(
        self, client_for, accountant, chart
    ):
        response = client_for(accountant).get(BUDGET_CODES_URL)

        assert response.status_code == status.HTTP_200_OK, response.data
        assert {row["code"] for row in response.data} == APPROVED
        assert {row["external_account_type"] for row in response.data} <= {
            "Revenue",
            "Other Income",
            "Other Expense",
        }

    def test_filter_ignores_the_structural_account_type_field(
        self, client_for, accountant, chart
    ):
        codes = {r["code"] for r in client_for(accountant).get(BUDGET_CODES_URL).data}

        assert "E-2" in codes  # account_type='view', external type approved
        assert "C-1" not in codes  # account_type='regular', external type not approved
        assert "B-1" not in codes  # blank external type

    def test_response_shape(self, client_for, accountant, chart):
        row = client_for(accountant).get(BUDGET_CODES_URL).data[0]

        assert set(row) == {"id", "code", "name", "external_account_type"}

    def test_requester_cannot_list(self, client_for, requester, chart):
        assert (
            client_for(requester).get(BUDGET_CODES_URL).status_code
            == status.HTTP_403_FORBIDDEN
        )

    def test_department_head_cannot_list(self, client_for, department_head, chart):
        assert (
            client_for(department_head).get(BUDGET_CODES_URL).status_code
            == status.HTTP_403_FORBIDDEN
        )

    def test_anonymous_is_rejected(self, anonymous_client, chart):
        assert (
            anonymous_client.get(BUDGET_CODES_URL).status_code
            == status.HTTP_401_UNAUTHORIZED
        )


class TestAssignItemBudgetCode:
    def test_accounts_assigns_and_it_persists(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["items"][0]["budget_code_id"] == chart["expense"].id
        item.refresh_from_db()
        assert item.budget_code_id == chart["expense"].id
        # The employee's category is untouched.
        assert item.category_id is not None

    def test_each_item_can_take_a_different_code(
        self, client_for, api_url, accountant, chart, category, pending_accounts_record
    ):
        first = pending_accounts_record.items.get()
        second = _second_item(pending_accounts_record, category)
        client = client_for(accountant)

        for item, key in ((first, "revenue"), (second, "income")):
            response = client.put(
                _url(api_url, pending_accounts_record, item),
                {"budget_code_id": chart[key].id},
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK, response.data

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.budget_code_id == chart["revenue"].id
        assert second.budget_code_id == chart["income"].id

    def test_assigning_one_item_leaves_the_others_alone(
        self, client_for, api_url, accountant, chart, category, pending_accounts_record
    ):
        first = pending_accounts_record.items.get()
        second = _second_item(pending_accounts_record, category)

        client_for(accountant).put(
            _url(api_url, pending_accounts_record, first),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        second.refresh_from_db()
        assert second.budget_code_id is None

    def test_accounts_can_change_an_existing_assignment(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()
        client = client_for(accountant)
        url = _url(api_url, pending_accounts_record, item)

        client.put(url, {"budget_code_id": chart["expense"].id}, format="json")
        client.put(url, {"budget_code_id": chart["revenue"].id}, format="json")

        item.refresh_from_db()
        assert item.budget_code_id == chart["revenue"].id

    @pytest.mark.parametrize("key", ["cash", "inventory", "blank"])
    def test_disallowed_account_type_is_rejected(
        self, client_for, api_url, accountant, chart, pending_accounts_record, key
    ):
        item = pending_accounts_record.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart[key].id},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "BUDGET_CODE_NOT_ALLOWED"
        item.refresh_from_db()
        assert item.budget_code_id is None

    def test_unknown_account_is_rejected(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": 9999999},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "BUDGET_CODE_NOT_ALLOWED"

    def test_missing_budget_code_id_is_400(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, item), {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_item_from_another_request_is_rejected(
        self, client_for, api_url, accountant, chart, requester,
        make_request_record, pending_accounts_record,
    ):
        other = make_request_record(requester, status="PENDING_ACCOUNTS")
        foreign_item = other.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, foreign_item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "ITEM_NOT_FOUND"
        foreign_item.refresh_from_db()
        assert foreign_item.budget_code_id is not None  # untouched fixture value

    @pytest.mark.parametrize(
        "record_status",
        [
            "DRAFT",
            "PENDING_DEPARTMENT_HEAD",
            "PENDING_GM",
            "PENDING_DIRECTOR",
            "PENDING_PROCUREMENT",
            "PROCESSED",
            "REJECTED",
        ],
    )
    def test_only_assignable_while_pending_accounts(
        self, client_for, api_url, accountant, chart, requester,
        make_request_record, record_status,
    ):
        record = make_request_record(requester, status=record_status)
        record.items.update(budget_code=None)
        item = record.items.get()

        response = client_for(accountant).put(
            _url(api_url, record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST, record_status
        assert response.data["code"] == "BUDGET_CODE_NOT_ASSIGNABLE"
        item.refresh_from_db()
        assert item.budget_code_id is None

    def test_employee_cannot_assign_even_on_their_own_request(
        self, client_for, api_url, requester, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(requester).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        item.refresh_from_db()
        assert item.budget_code_id is None

    def test_department_head_cannot_assign(
        self, client_for, api_url, department_head, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(department_head).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_accountant_cannot_assign_on_their_own_request(
        self, client_for, api_url, accountant, chart, make_request_record
    ):
        record = make_request_record(accountant, status="PENDING_ACCOUNTS")
        record.items.update(budget_code=None)
        item = record.items.get()

        response = client_for(accountant).put(
            _url(api_url, record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_is_rejected(
        self, anonymous_client, api_url, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = anonymous_client.put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVerificationAfterAssignment:
    def _verify(self, client_for, api_url, accountant, record):
        return client_for(accountant).post(f"{api_url}{record.id}/accounts/verify/")

    def test_verify_is_blocked_before_assignment(
        self, client_for, api_url, accountant, pending_accounts_record
    ):
        response = self._verify(client_for, api_url, accountant, pending_accounts_record)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "BUDGET_CODE_NOT_ASSIGNED"
        pending_accounts_record.refresh_from_db()
        assert pending_accounts_record.status == "PENDING_ACCOUNTS"

    def test_verify_is_still_blocked_when_only_some_items_are_assigned(
        self, client_for, api_url, accountant, chart, category, pending_accounts_record
    ):
        first = pending_accounts_record.items.get()
        _second_item(pending_accounts_record, category)
        client_for(accountant).put(
            _url(api_url, pending_accounts_record, first),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )

        response = self._verify(client_for, api_url, accountant, pending_accounts_record)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "BUDGET_CODE_NOT_ASSIGNED"

    def test_verify_succeeds_once_every_item_is_assigned(
        self, client_for, api_url, accountant, chart, category, pending_accounts_record
    ):
        first = pending_accounts_record.items.get()
        second = _second_item(pending_accounts_record, category)
        client = client_for(accountant)
        for item, key in ((first, "expense"), (second, "revenue")):
            client.put(
                _url(api_url, pending_accounts_record, item),
                {"budget_code_id": chart[key].id},
                format="json",
            )

        response = self._verify(client_for, api_url, accountant, pending_accounts_record)

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == "PENDING_GM"
        pending_accounts_record.refresh_from_db()
        assert pending_accounts_record.status == "PENDING_GM"

    def test_assignment_is_frozen_after_verification(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()
        client = client_for(accountant)
        client.put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["expense"].id},
            format="json",
        )
        self._verify(client_for, api_url, accountant, pending_accounts_record)

        response = client.put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["revenue"].id},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        item.refresh_from_db()
        assert item.budget_code_id == chart["expense"].id


class TestBudgetCodeSerialization:
    """What Accounts sees: the actual assigned AccountChart code."""

    def test_assigned_item_exposes_the_actual_accountchart_code_and_name(
        self, client_for, api_url, requester, accountant, make_request_record, budget_code
    ):
        record = make_request_record(requester, status="PROCESSED")

        response = client_for(accountant).get(f"{api_url}{record.id}/")

        item = response.data["items"][0]
        assert item["budget_code_id"] == budget_code.id
        assert item["budget_code"] == {
            "id": budget_code.id,
            "code": budget_code.code,
            "name": budget_code.name,
        }

    def test_budget_code_is_not_derived_from_the_category(
        self, client_for, api_url, requester, accountant, make_request_record,
        category, budget_code,
    ):
        """category maps to a different AccountChart than the one Accounts assigned."""
        record = make_request_record(requester, status="PROCESSED")

        item = client_for(accountant).get(f"{api_url}{record.id}/").data["items"][0]

        assert item["category"]["id"] == category.id
        assert category.account_chart.code != budget_code.code
        assert item["budget_code"]["code"] == budget_code.code

    def test_unassigned_item_has_null_budget_code_for_accounts(
        self, client_for, api_url, requester, accountant, make_request_record, category
    ):
        record = make_request_record(requester, status="PENDING_ACCOUNTS")
        record.items.update(budget_code=None)

        item = client_for(accountant).get(f"{api_url}{record.id}/").data["items"][0]

        assert item["budget_code_id"] is None
        assert item["budget_code"] is None
        assert item["category"]["id"] == category.id

    def test_assignment_response_carries_the_new_code(
        self, client_for, api_url, accountant, chart, pending_accounts_record
    ):
        item = pending_accounts_record.items.get()

        response = client_for(accountant).put(
            _url(api_url, pending_accounts_record, item),
            {"budget_code_id": chart["revenue"].id},
            format="json",
        )

        assert response.data["items"][0]["budget_code"]["code"] == "R-1"
        assert response.data["items"][0]["budget_code_id"] == chart["revenue"].id

    def test_mixed_items_serialize_each_their_own_code(
        self, client_for, api_url, requester, accountant, category,
        make_request_record, chart,
    ):
        record = make_request_record(requester, status="PENDING_ACCOUNTS")
        first = record.items.get()
        first.budget_code = chart["expense"]
        first.save()
        _second_item(record, category)  # unassigned

        items = client_for(accountant).get(f"{api_url}{record.id}/").data["items"]

        by_desc = {i["description"]: i for i in items}
        assert by_desc["Laptop"]["budget_code"]["code"] == "E-1"
        assert by_desc["Monitor"]["budget_code"] is None


class TestBudgetCodeDisclosure:
    """F25: budget_code / budget_code_id are Finance and Procurement only."""

    KEYS = ("budget_code", "budget_code_id")

    def _item(self, client_for, api_url, actor, record):
        response = client_for(actor).get(f"{api_url}{record.id}/")
        assert response.status_code == status.HTTP_200_OK, response.data
        return response.data["items"][0]

    def test_requester_receives_neither_key_on_their_own_assigned_request(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="PROCESSED")  # has a code

        item = self._item(client_for, api_url, requester, record)

        for key in self.KEYS:
            assert key not in item
        assert item["category_id"] is not None  # category still served

    def test_ordinary_viewer_receives_neither_key(
        self, client_for, api_url, requester, make_employee, make_request_record
    ):
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        viewer = make_employee("Vera Viewer", [P.VIEW])
        record = make_request_record(requester, status="PROCESSED")

        item = self._item(client_for, api_url, viewer, record)

        for key in self.KEYS:
            assert key not in item

    def test_gm_and_director_do_not_receive_them(
        self, client_for, api_url, requester, general_manager, director,
        make_request_record,
    ):
        record = make_request_record(requester, status="PROCESSED")

        for actor in (general_manager, director):
            item = self._item(client_for, api_url, actor, record)
            for key in self.KEYS:
                assert key not in item

    def test_accounts_receives_both(
        self, client_for, api_url, requester, accountant, make_request_record, budget_code
    ):
        record = make_request_record(requester, status="PROCESSED")

        item = self._item(client_for, api_url, accountant, record)

        assert item["budget_code_id"] == budget_code.id
        assert item["budget_code"]["code"] == budget_code.code

    def test_procurement_receives_both(
        self, client_for, api_url, requester, procurement_officer,
        make_request_record, budget_code,
    ):
        record = make_request_record(requester, status="PROCESSED")

        item = self._item(client_for, api_url, procurement_officer, record)

        assert item["budget_code_id"] == budget_code.id
        assert item["budget_code"]["code"] == budget_code.code

    @pytest.mark.parametrize("actor_fixture", ["accountant", "procurement_officer"])
    def test_unassigned_is_null_for_finance_and_procurement(
        self, request, client_for, api_url, requester, make_request_record, actor_fixture
    ):
        actor = request.getfixturevalue(actor_fixture)
        record = make_request_record(requester, status="PENDING_ACCOUNTS")
        record.items.update(budget_code=None)

        item = self._item(client_for, api_url, actor, record)

        assert item["budget_code_id"] is None
        assert item["budget_code"] is None

    def test_unassigned_omits_the_keys_for_a_requester_rather_than_nulling_them(
        self, client_for, api_url, requester, make_request_record
    ):
        record = make_request_record(requester, status="PENDING_ACCOUNTS")
        record.items.update(budget_code=None)

        item = self._item(client_for, api_url, requester, record)

        for key in self.KEYS:
            assert key not in item

    def test_create_response_applies_the_same_rule(
        self, client_for, api_url, requester, valid_payload
    ):
        """Create goes through the same central serializer path."""
        created = client_for(requester).post(api_url, valid_payload, format="json")
        assert created.status_code == status.HTTP_201_CREATED, created.data

        for key in self.KEYS:
            assert key not in created.data["items"][0]

    def test_rule_is_capability_based_not_identity_based(
        self, client_for, api_url, make_employee, make_request_record, budget_code
    ):
        """A requester who also holds process is treated as Procurement."""
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        both = make_employee("Bea Both", [P.CREATE, P.VIEW, P.PROCESS])
        record = make_request_record(both, status="PROCESSED")

        item = self._item(client_for, api_url, both, record)

        assert item["budget_code"]["code"] == budget_code.code

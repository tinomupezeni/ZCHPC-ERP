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

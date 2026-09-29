"""
F25 Slice 2 - unit tests for the budget-code assignment domain rule and use cases.
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.application.use_cases import (
    AssignItemBudgetCode,
    ListAssignableBudgetCodes,
)
from modules.procurement.domain.budget_code_rules import (
    ALLOWED_BUDGET_CODE_EXTERNAL_TYPES,
    BudgetCode,
)
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from shared.domain.exceptions import AuthorizationError, ValidationError

REQUESTER_ID = 10
ACCOUNTS_ID = 20


def _actor(employee_id, permissions):
    return Actor(
        employee_id=employee_id,
        permissions=PermissionSet.from_list(permissions),
        department_id=1,
    )


ACCOUNTS = _actor(ACCOUNTS_ID, ["procurement.purchase_request.accounts_verify"])
REQUESTER = _actor(REQUESTER_ID, ["procurement.purchase_request.create"])


class _Directory:
    def get_headed_department_ids(self, employee_id):
        return set()


@pytest.fixture
def policy():
    return PurchaseRequestAuthorizationPolicy(directory=_Directory())


@pytest.fixture
def pending_request():
    request = PurchaseRequest.create(
        requester_id=REQUESTER_ID,
        requester_name="Riley",
        department_id=1,
        department_name="IT",
        designation="Dev",
        contact="x",
    )
    request._id = 100
    for n, description in enumerate(("Laptop", "Monitor"), start=1):
        item = PurchaseRequestItem(
            description=description,
            quantity=1,
            expected_delivery_period="1 week",
            estimated_cost=Decimal("10.00"),
            category_id=1,
        )
        item._id = n
        request.add_item(item)
    request.status = RequestStatus.PENDING_ACCOUNTS
    return request


@pytest.fixture
def repository(pending_request):
    repo = Mock()
    repo.get_by_id.return_value = pending_request
    repo.save.side_effect = lambda r: r
    return repo


@pytest.fixture
def budget_codes():
    repo = Mock()
    repo.get_assignable_by_id.side_effect = lambda i: (
        BudgetCode(id=i, code="E-1", name="Expense", external_account_type="Other Expense")
        if i == 5
        else None
    )
    repo.get_assignable.return_value = [
        BudgetCode(id=5, code="E-1", name="Expense", external_account_type="Other Expense")
    ]
    return repo


def test_approved_types_are_exactly_the_three_finance_confirmed_ones():
    assert ALLOWED_BUDGET_CODE_EXTERNAL_TYPES == {
        "Revenue",
        "Other Income",
        "Other Expense",
    }


class TestDomainAssignBudgetCode:
    def test_assigns_only_the_named_item(self, pending_request):
        pending_request.assign_budget_code(2, 5)

        assert pending_request.items[0].budget_code_id is None
        assert pending_request.items[1].budget_code_id == 5

    @pytest.mark.parametrize(
        "status",
        [s for s in RequestStatus if s != RequestStatus.PENDING_ACCOUNTS],
    )
    def test_rejected_outside_pending_accounts(self, pending_request, status):
        pending_request.status = status

        with pytest.raises(ValidationError) as exc:
            pending_request.assign_budget_code(1, 5)

        assert exc.value.code == "BUDGET_CODE_NOT_ASSIGNABLE"
        assert pending_request.items[0].budget_code_id is None

    def test_unknown_item_is_rejected(self, pending_request):
        with pytest.raises(ValidationError) as exc:
            pending_request.assign_budget_code(999, 5)

        assert exc.value.code == "ITEM_NOT_FOUND"


class TestAssignItemBudgetCodeUseCase:
    def test_assigns_and_saves(self, repository, policy, budget_codes, pending_request):
        result = AssignItemBudgetCode(repository, policy, budget_codes).execute(
            100, 1, 5, ACCOUNTS
        )

        assert result.items[0].budget_code_id == 5
        repository.save.assert_called_once_with(pending_request)

    def test_disallowed_code_is_rejected_and_nothing_saved(
        self, repository, policy, budget_codes, pending_request
    ):
        with pytest.raises(ValidationError) as exc:
            AssignItemBudgetCode(repository, policy, budget_codes).execute(
                100, 1, 6, ACCOUNTS
            )

        assert exc.value.code == "BUDGET_CODE_NOT_ALLOWED"
        assert pending_request.items[0].budget_code_id is None
        repository.save.assert_not_called()

    def test_requires_accounts_capability(
        self, repository, policy, budget_codes, pending_request
    ):
        with pytest.raises(AuthorizationError):
            AssignItemBudgetCode(repository, policy, budget_codes).execute(
                100, 1, 5, REQUESTER
            )

        repository.save.assert_not_called()

    def test_requester_cannot_assign_to_their_own_request(
        self, repository, policy, budget_codes
    ):
        requester_with_accounts = _actor(
            REQUESTER_ID, ["procurement.purchase_request.accounts_verify"]
        )

        with pytest.raises(AuthorizationError):
            AssignItemBudgetCode(repository, policy, budget_codes).execute(
                100, 1, 5, requester_with_accounts
            )


class TestListAssignableBudgetCodesUseCase:
    def test_accounts_gets_the_repository_list(self, policy, budget_codes):
        result = ListAssignableBudgetCodes(budget_codes, policy).execute(ACCOUNTS)

        assert [c.id for c in result] == [5]

    def test_non_accounts_actor_is_refused(self, policy, budget_codes):
        with pytest.raises(AuthorizationError):
            ListAssignableBudgetCodes(budget_codes, policy).execute(REQUESTER)

        budget_codes.get_assignable.assert_not_called()

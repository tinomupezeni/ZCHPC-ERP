"""
Tests for purchase request application use cases.

These cover orchestration (load -> domain -> save) and domain error
propagation. Each use case now authorizes before invoking the domain, so the
tests supply an actor that is authorized for the operation under test; who is
allowed to do what is covered in tests/application/authorization/.

Follows existing project conventions:
- class-based test organization (TestXxx)
- pytest fixtures for shared setup
- Mock repository injected via constructor
"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.application.use_cases.purchase_request_use_cases import (
    ApprovePurchaseRequestByDepartmentHead,
    ApprovePurchaseRequestByDirector,
    CorrectAndResubmitPurchaseRequest,
    CreatePurchaseRequest,
    CreatePurchaseRequestDTO,
    ProcessPurchaseRequestByProcurement,
    PurchaseRequestItemDTO,
    RecommendPurchaseRequestByGM,
    RejectPurchaseRequest,
    SubmitPurchaseRequest,
    VerifyPurchaseRequestByAccounts,
    ViewPurchaseRequest,
)
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from shared.domain.exceptions import NotFoundError, ValidationError

REQUESTER_ID = 1
DEPARTMENT_ID = 10
DEPARTMENT_HEAD_ID = 20


class StubDirectory:
    """Records employee #20 as the head of the department under test."""

    def get_department_head_id(self, department_id):
        return DEPARTMENT_HEAD_ID if department_id == DEPARTMENT_ID else None

    def get_department_id(self, employee_id):  # noqa: ARG002 - not used by these tests
        return DEPARTMENT_ID


def authorized_actor(employee_id, department_id=DEPARTMENT_ID):
    """An actor holding every procurement capability, for orchestration tests."""
    return Actor(
        employee_id=employee_id,
        permissions=PermissionSet.from_list(["procurement.*"]),
        department_id=department_id,
    )


@pytest.fixture
def repository():
    repo = Mock()
    repo.save.side_effect = lambda x: x
    return repo


@pytest.fixture
def category_repository():
    """
    Stub category repository (Slice F11-A).

    Category #1 is active and resolves to AccountChart #77; category #2
    exists but is inactive; category #3 does not exist at all
    (get_by_id returns None).
    """
    repo = Mock()

    def get_by_id(category_id):
        if category_id == 1:
            return SimpleNamespace(id=1, name="IT Consumables", account_chart_id=77, is_active=True)
        if category_id == 2:
            return SimpleNamespace(id=2, name="Discontinued", account_chart_id=88, is_active=False)
        return None

    repo.get_by_id.side_effect = get_by_id
    return repo


@pytest.fixture
def policy():
    return PurchaseRequestAuthorizationPolicy(directory=StubDirectory())


@pytest.fixture
def requester():
    """The employee who raised the request under test."""
    return authorized_actor(REQUESTER_ID)


@pytest.fixture
def draft_request_with_item():
    """A DRAFT PurchaseRequest with one item, ready for submission."""
    req = PurchaseRequest.create(
        requester_id=REQUESTER_ID,
        requester_name="John Doe",
        department_id=DEPARTMENT_ID,
        department_name="IT",
        designation="Developer",
        contact="ext 123",
    )
    req._id = 100
    item = PurchaseRequestItem(
        description="Laptop",
        quantity=1,
        expected_delivery_period="2 weeks",
        estimated_cost=Decimal("1500.00"),
        budget_code_id=5,
    )
    req.add_item(item)
    return req


class TestCreatePurchaseRequest:
    """Tests for the CreatePurchaseRequest use case."""

    def test_creates_request_with_items(self, repository, policy, category_repository, requester):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = CreatePurchaseRequestDTO(
            requester_id=REQUESTER_ID,
            requester_name="Jane Doe",
            department_id=2,
            department_name="HR",
            designation="Manager",
            contact="123",
            items=[
                PurchaseRequestItemDTO(
                    description="Desk",
                    quantity=2,
                    expected_delivery_period="1 week",
                    estimated_cost=Decimal("500.00"),
                    budget_code_id=10,
                )
            ],
        )

        result = use_case.execute(dto, requester)

        assert result.requester_name == "Jane Doe"
        assert result.department_name == "HR"
        assert result.designation == "Manager"
        assert len(result.items) == 1
        assert result.items[0].description == "Desk"
        assert result.items[0].budget_code_id == 10
        assert result.status == RequestStatus.DRAFT
        repository.save.assert_called_once()

    def test_creates_request_without_items(self, repository, policy, category_repository, requester):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = CreatePurchaseRequestDTO(
            requester_id=REQUESTER_ID,
            requester_name="Jane Doe",
            department_id=2,
            department_name="HR",
            designation="Manager",
            contact="123",
        )

        result = use_case.execute(dto, requester)

        assert result.status == RequestStatus.DRAFT
        assert len(result.items) == 0
        repository.save.assert_called_once()


class TestCreatePurchaseRequestCategoryResolution:
    """
    Slice F11-A: category_id -> budget_code_id resolution, entirely inside
    CreatePurchaseRequest._resolve_budget_code_id. No keyword matching, no
    description-based inference is exercised or possible here - the stub
    category_repository only ever answers by category_id.
    """

    def _item(self, **overrides):
        defaults = {
            "description": "Keyboard",
            "quantity": 1,
            "expected_delivery_period": "2 weeks",
            "estimated_cost": Decimal("50.00"),
        }
        defaults.update(overrides)
        return PurchaseRequestItemDTO(**defaults)

    def _dto(self, item):
        return CreatePurchaseRequestDTO(
            requester_id=REQUESTER_ID,
            requester_name="Jane Doe",
            department_id=2,
            department_name="HR",
            designation="Manager",
            contact="123",
            items=[item],
        )

    def test_active_category_resolves_to_its_account_chart_id(
        self, repository, policy, category_repository, requester
    ):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(self._item(category_id=1))

        result = use_case.execute(dto, requester)

        assert result.items[0].budget_code_id == 77
        category_repository.get_by_id.assert_called_once_with(1)

    def test_unknown_category_raises_validation_error(
        self, repository, policy, category_repository, requester
    ):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(self._item(category_id=999))

        with pytest.raises(ValidationError) as exc:
            use_case.execute(dto, requester)

        assert exc.value.code == "CATEGORY_NOT_FOUND"
        repository.save.assert_not_called()

    def test_inactive_category_raises_validation_error(
        self, repository, policy, category_repository, requester
    ):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(self._item(category_id=2))

        with pytest.raises(ValidationError) as exc:
            use_case.execute(dto, requester)

        assert exc.value.code == "CATEGORY_INACTIVE"
        repository.save.assert_not_called()

    def test_neither_category_nor_budget_code_raises_validation_error(
        self, repository, policy, category_repository, requester
    ):
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(self._item())

        with pytest.raises(ValidationError) as exc:
            use_case.execute(dto, requester)

        assert exc.value.code == "MISSING_BUDGET_CLASSIFICATION"
        repository.save.assert_not_called()

    def test_category_id_wins_even_if_budget_code_id_is_also_supplied(
        self, repository, policy, category_repository, requester
    ):
        """
        The employee must not be able to control the resulting GL account by
        also supplying budget_code_id - category_id, when present, is
        authoritative regardless. (The API serializer separately rejects
        this combination outright; this pins the use case's own guarantee
        for any caller that reaches it directly.)
        """
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(self._item(category_id=1, budget_code_id=999999))

        result = use_case.execute(dto, requester)

        assert result.items[0].budget_code_id == 77

    def test_description_never_influences_resolution(
        self, repository, policy, category_repository, requester
    ):
        """
        No keyword/description-based classification exists anywhere in this
        path - the exact same category_id resolves identically regardless
        of what the item's free-text description says.
        """
        use_case = CreatePurchaseRequest(repository, policy, category_repository)
        dto = self._dto(
            self._item(category_id=1, description="Completely unrelated text about fuel and travel")
        )

        result = use_case.execute(dto, requester)

        assert result.items[0].budget_code_id == 77


class TestViewPurchaseRequest:
    """Tests for the ViewPurchaseRequest use case."""

    def test_returns_the_request(self, repository, policy, requester, draft_request_with_item):
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ViewPurchaseRequest(repository, policy)

        result = use_case.execute(100, requester)

        assert result is draft_request_with_item
        repository.get_by_id.assert_called_once_with(100)
        repository.save.assert_not_called()

    def test_not_found_raises(self, repository, policy, requester):
        repository.get_by_id.return_value = None
        use_case = ViewPurchaseRequest(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, requester)


class TestSubmitPurchaseRequest:
    """Tests for the SubmitPurchaseRequest use case."""

    def test_submits_draft_request(self, repository, policy, requester, draft_request_with_item):
        repository.get_by_id.return_value = draft_request_with_item
        use_case = SubmitPurchaseRequest(repository, policy)

        result = use_case.execute(100, requester)

        assert result.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.get_by_id.assert_called_once_with(100)
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy, requester):
        repository.get_by_id.return_value = None
        use_case = SubmitPurchaseRequest(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, requester)
        repository.save.assert_not_called()

    def test_invalid_state_raises(self, repository, policy, requester, draft_request_with_item):
        draft_request_with_item.status = RequestStatus.PENDING_ACCOUNTS
        repository.get_by_id.return_value = draft_request_with_item
        use_case = SubmitPurchaseRequest(repository, policy)

        with pytest.raises(ValidationError):
            use_case.execute(100, requester)
        repository.save.assert_not_called()


class TestApprovePurchaseRequestByDepartmentHead:
    """Tests for the ApprovePurchaseRequestByDepartmentHead use case."""

    def test_approves_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDepartmentHead(repository, policy)

        result = use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID))

        assert result.status == RequestStatus.PENDING_ACCOUNTS
        assert result.decisions[-1].actor_id == 20
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = ApprovePurchaseRequestByDepartmentHead(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(DEPARTMENT_HEAD_ID))
        repository.save.assert_not_called()

    def test_invalid_state_raises(self, repository, policy, draft_request_with_item):
        """Cannot approve a DRAFT request (must be PENDING_DEPARTMENT_HEAD)."""
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDepartmentHead(repository, policy)

        with pytest.raises(ValidationError):
            use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID))
        repository.save.assert_not_called()


class TestVerifyPurchaseRequestByAccounts:
    """Tests for the VerifyPurchaseRequestByAccounts use case."""

    def test_verifies_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = VerifyPurchaseRequestByAccounts(repository, policy)

        result = use_case.execute(100, authorized_actor(21))

        assert result.status == RequestStatus.PENDING_GM
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = VerifyPurchaseRequestByAccounts(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(21))
        repository.save.assert_not_called()


class TestRecommendPurchaseRequestByGM:
    """Tests for the RecommendPurchaseRequestByGM use case."""

    def test_recommends_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RecommendPurchaseRequestByGM(repository, policy)

        result = use_case.execute(100, authorized_actor(22))

        assert result.status == RequestStatus.PENDING_DIRECTOR
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = RecommendPurchaseRequestByGM(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(22))
        repository.save.assert_not_called()


class TestApprovePurchaseRequestByDirector:
    """Tests for the ApprovePurchaseRequestByDirector use case."""

    def test_approves_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        draft_request_with_item.recommend_by_gm(22)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDirector(repository, policy)

        result = use_case.execute(100, authorized_actor(23))

        assert result.status == RequestStatus.PENDING_PROCUREMENT
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = ApprovePurchaseRequestByDirector(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(23))
        repository.save.assert_not_called()


class TestProcessPurchaseRequestByProcurement:
    """Tests for the ProcessPurchaseRequestByProcurement use case."""

    def test_processes_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        draft_request_with_item.recommend_by_gm(22)
        draft_request_with_item.approve_by_director(23)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ProcessPurchaseRequestByProcurement(repository, policy)

        result = use_case.execute(100, authorized_actor(24))

        assert result.status == RequestStatus.PROCESSED
        assert result.processed_by == 24
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = ProcessPurchaseRequestByProcurement(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(24))
        repository.save.assert_not_called()


class TestRejectPurchaseRequest:
    """Tests for the RejectPurchaseRequest use case."""

    def test_rejects_pending_request(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository, policy)

        result = use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID), reason="Too expensive")

        assert result.status == RequestStatus.REJECTED
        assert result.decisions[-1].reason == "Too expensive"
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = RejectPurchaseRequest(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(DEPARTMENT_HEAD_ID), reason="Not needed")
        repository.save.assert_not_called()

    def test_empty_reason_raises(self, repository, policy, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository, policy)

        with pytest.raises(ValidationError):
            use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID), reason="")
        repository.save.assert_not_called()

    def test_reject_from_invalid_state_raises(
        self, repository, policy, draft_request_with_item
    ):
        """Cannot reject a DRAFT request."""
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository, policy)

        with pytest.raises(ValidationError):
            use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID), reason="Not needed")
        repository.save.assert_not_called()


class TestCorrectAndResubmitPurchaseRequest:
    """Tests for the CorrectAndResubmitPurchaseRequest use case."""

    def test_corrects_rejected_request(
        self, repository, policy, requester, draft_request_with_item
    ):
        draft_request_with_item.submit()
        draft_request_with_item.reject(actor_id=25, reason="Too expensive")
        repository.get_by_id.return_value = draft_request_with_item
        use_case = CorrectAndResubmitPurchaseRequest(repository, policy)

        result = use_case.execute(100, requester)

        assert result.status == RequestStatus.DRAFT
        repository.save.assert_called_once_with(draft_request_with_item)

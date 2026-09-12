"""
Tests for purchase request application use cases.

Follows existing project conventions:
- class-based test organization (TestXxx)
- pytest fixtures for shared setup
- Mock repository injected via constructor
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal

from shared.domain.exceptions import NotFoundError, ValidationError
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from modules.procurement.application.use_cases.purchase_request_use_cases import (
    CreatePurchaseRequest,
    CreatePurchaseRequestDTO,
    PurchaseRequestItemDTO,
    SubmitPurchaseRequest,
    ApprovePurchaseRequestByDepartmentHead,
    VerifyPurchaseRequestByAccounts,
    RecommendPurchaseRequestByGM,
    ApprovePurchaseRequestByDirector,
    ProcessPurchaseRequestByProcurement,
    RejectPurchaseRequest,
    CorrectAndResubmitPurchaseRequest,
)


@pytest.fixture
def repository():
    repo = Mock()
    repo.save.side_effect = lambda x: x
    return repo


@pytest.fixture
def draft_request_with_item():
    """A DRAFT PurchaseRequest with one item, ready for submission."""
    req = PurchaseRequest.create(
        requester_id=1,
        requester_name="John Doe",
        department_id=10,
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

    def test_creates_request_with_items(self, repository):
        use_case = CreatePurchaseRequest(repository)
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
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

        result = use_case.execute(dto)

        assert result.requester_name == "Jane Doe"
        assert result.department_name == "HR"
        assert result.designation == "Manager"
        assert len(result.items) == 1
        assert result.items[0].description == "Desk"
        assert result.status == RequestStatus.DRAFT
        repository.save.assert_called_once()

    def test_creates_request_without_items(self, repository):
        use_case = CreatePurchaseRequest(repository)
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
            requester_name="Jane Doe",
            department_id=2,
            department_name="HR",
            designation="Manager",
            contact="123",
        )

        result = use_case.execute(dto)

        assert result.status == RequestStatus.DRAFT
        assert len(result.items) == 0
        repository.save.assert_called_once()


class TestSubmitPurchaseRequest:
    """Tests for the SubmitPurchaseRequest use case."""

    def test_submits_draft_request(self, repository, draft_request_with_item):
        repository.get_by_id.return_value = draft_request_with_item
        use_case = SubmitPurchaseRequest(repository)

        result = use_case.execute(100)

        assert result.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.get_by_id.assert_called_once_with(100)
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = SubmitPurchaseRequest(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999)
        repository.save.assert_not_called()

    def test_invalid_state_raises(self, repository, draft_request_with_item):
        draft_request_with_item.status = RequestStatus.PENDING_ACCOUNTS
        repository.get_by_id.return_value = draft_request_with_item
        use_case = SubmitPurchaseRequest(repository)

        with pytest.raises(ValidationError):
            use_case.execute(100)
        repository.save.assert_not_called()


class TestApprovePurchaseRequestByDepartmentHead:
    """Tests for the ApprovePurchaseRequestByDepartmentHead use case."""

    def test_approves_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDepartmentHead(repository)

        result = use_case.execute(100, actor_id=20)

        assert result.status == RequestStatus.PENDING_ACCOUNTS
        assert result.decisions[-1].actor_id == 20
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = ApprovePurchaseRequestByDepartmentHead(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=20)
        repository.save.assert_not_called()

    def test_invalid_state_raises(self, repository, draft_request_with_item):
        """Cannot approve a DRAFT request (must be PENDING_DEPARTMENT_HEAD)."""
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDepartmentHead(repository)

        with pytest.raises(ValidationError):
            use_case.execute(100, actor_id=20)
        repository.save.assert_not_called()


class TestVerifyPurchaseRequestByAccounts:
    """Tests for the VerifyPurchaseRequestByAccounts use case."""

    def test_verifies_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = VerifyPurchaseRequestByAccounts(repository)

        result = use_case.execute(100, actor_id=21)

        assert result.status == RequestStatus.PENDING_GM
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = VerifyPurchaseRequestByAccounts(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=21)
        repository.save.assert_not_called()


class TestRecommendPurchaseRequestByGM:
    """Tests for the RecommendPurchaseRequestByGM use case."""

    def test_recommends_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RecommendPurchaseRequestByGM(repository)

        result = use_case.execute(100, actor_id=22)

        assert result.status == RequestStatus.PENDING_DIRECTOR
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = RecommendPurchaseRequestByGM(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=22)
        repository.save.assert_not_called()


class TestApprovePurchaseRequestByDirector:
    """Tests for the ApprovePurchaseRequestByDirector use case."""

    def test_approves_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        draft_request_with_item.recommend_by_gm(22)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ApprovePurchaseRequestByDirector(repository)

        result = use_case.execute(100, actor_id=23)

        assert result.status == RequestStatus.PENDING_PROCUREMENT
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = ApprovePurchaseRequestByDirector(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=23)
        repository.save.assert_not_called()


class TestProcessPurchaseRequestByProcurement:
    """Tests for the ProcessPurchaseRequestByProcurement use case."""

    def test_processes_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        draft_request_with_item.recommend_by_gm(22)
        draft_request_with_item.approve_by_director(23)
        repository.get_by_id.return_value = draft_request_with_item
        use_case = ProcessPurchaseRequestByProcurement(repository)

        result = use_case.execute(100, actor_id=24)

        assert result.status == RequestStatus.PROCESSED
        assert result.processed_by == 24
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = ProcessPurchaseRequestByProcurement(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=24)
        repository.save.assert_not_called()


class TestRejectPurchaseRequest:
    """Tests for the RejectPurchaseRequest use case."""

    def test_rejects_pending_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository)

        result = use_case.execute(100, actor_id=25, reason="Too expensive")

        assert result.status == RequestStatus.REJECTED
        assert result.decisions[-1].reason == "Too expensive"
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = RejectPurchaseRequest(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999, actor_id=25, reason="Not needed")
        repository.save.assert_not_called()

    def test_empty_reason_raises(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository)

        with pytest.raises(ValidationError):
            use_case.execute(100, actor_id=25, reason="")
        repository.save.assert_not_called()

    def test_reject_from_invalid_state_raises(
        self, repository, draft_request_with_item
    ):
        """Cannot reject a DRAFT request."""
        repository.get_by_id.return_value = draft_request_with_item
        use_case = RejectPurchaseRequest(repository)

        with pytest.raises(ValidationError):
            use_case.execute(100, actor_id=25, reason="Not needed")
        repository.save.assert_not_called()


class TestCorrectAndResubmitPurchaseRequest:
    """Tests for the CorrectAndResubmitPurchaseRequest use case."""

    def test_corrects_rejected_request(self, repository, draft_request_with_item):
        draft_request_with_item.submit()
        draft_request_with_item.reject(actor_id=25, reason="Too expensive")
        repository.get_by_id.return_value = draft_request_with_item
        use_case = CorrectAndResubmitPurchaseRequest(repository)

        result = use_case.execute(100)

        assert result.status == RequestStatus.DRAFT
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_not_found_raises(self, repository):
        repository.get_by_id.return_value = None
        use_case = CorrectAndResubmitPurchaseRequest(repository)

        with pytest.raises(NotFoundError):
            use_case.execute(999)
        repository.save.assert_not_called()

    def test_correct_from_draft_raises(self, repository, draft_request_with_item):
        """Cannot correct a DRAFT request — only REJECTED ones."""
        repository.get_by_id.return_value = draft_request_with_item
        use_case = CorrectAndResubmitPurchaseRequest(repository)

        with pytest.raises(ValidationError):
            use_case.execute(100)
        repository.save.assert_not_called()

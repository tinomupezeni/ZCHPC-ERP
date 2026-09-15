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
    DeletePurchaseRequest,
    ProcessPurchaseRequestByProcurement,
    PurchaseRequestItemDTO,
    RecommendPurchaseRequestByGM,
    RejectPurchaseRequest,
    SubmitPurchaseRequest,
    UpdatePurchaseRequestItemDTO,
    UpdatePurchaseRequestItems,
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

    def test_publishes_purchase_request_processed_after_save(
        self, repository, policy, draft_request_with_item
    ):
        """
        Slice 3 notifications: the event bus must be given whatever domain
        events process_by_procurement() recorded on `request` - not events
        read off the use case's return value, since the real repository's
        save() reconstructs and returns a different PurchaseRequest instance
        (see ProcessPurchaseRequestByProcurement's docstring).
        """
        from modules.procurement.domain.events import PurchaseRequestProcessed

        draft_request_with_item.submit()
        draft_request_with_item.approve_by_department_head(20)
        draft_request_with_item.verify_by_accounts(21)
        draft_request_with_item.recommend_by_gm(22)
        draft_request_with_item.approve_by_director(23)
        repository.get_by_id.return_value = draft_request_with_item
        event_bus = Mock()
        use_case = ProcessPurchaseRequestByProcurement(repository, policy, event_bus=event_bus)

        use_case.execute(100, authorized_actor(24))

        event_bus.publish_all.assert_called_once()
        (published,), _ = event_bus.publish_all.call_args
        assert len(published) == 1
        assert isinstance(published[0], PurchaseRequestProcessed)
        assert published[0].request_id == draft_request_with_item.id
        assert published[0].processed_by == 24
        # Events must not still be sitting on the aggregate after publishing.
        assert draft_request_with_item.domain_events == []

    def test_does_not_publish_when_processing_fails(
        self, repository, policy, draft_request_with_item
    ):
        """A DRAFT request can't be processed - no save, no event, no notification."""
        repository.get_by_id.return_value = draft_request_with_item
        event_bus = Mock()
        use_case = ProcessPurchaseRequestByProcurement(repository, policy, event_bus=event_bus)

        with pytest.raises(ValidationError):
            use_case.execute(100, authorized_actor(24))

        repository.save.assert_not_called()
        event_bus.publish_all.assert_not_called()


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

    def test_publishes_purchase_request_rejected_after_save(
        self, repository, policy, draft_request_with_item
    ):
        """Slice 3 notifications - see the equivalent Process test for why events are read from `request`, not the use case's return value."""
        from modules.procurement.domain.events import PurchaseRequestRejected

        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        event_bus = Mock()
        use_case = RejectPurchaseRequest(repository, policy, event_bus=event_bus)

        use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID), reason="Too expensive")

        event_bus.publish_all.assert_called_once()
        (published,), _ = event_bus.publish_all.call_args
        assert len(published) == 1
        assert isinstance(published[0], PurchaseRequestRejected)
        assert published[0].request_id == draft_request_with_item.id
        assert published[0].rejector_id == DEPARTMENT_HEAD_ID
        assert published[0].reason == "Too expensive"
        assert draft_request_with_item.domain_events == []

    def test_does_not_publish_on_retry_after_already_rejected(
        self, repository, policy, draft_request_with_item
    ):
        """
        Idempotency (Slice 3): rejecting an already-REJECTED request (e.g. a
        retried call) fails the domain guard before any save or publish, so a
        retry can never create a second notification for the same rejection.
        """
        draft_request_with_item.submit()
        draft_request_with_item.reject(DEPARTMENT_HEAD_ID, "Too expensive")
        repository.get_by_id.return_value = draft_request_with_item
        draft_request_with_item.clear_domain_events()  # as the first, successful call would have
        event_bus = Mock()
        use_case = RejectPurchaseRequest(repository, policy, event_bus=event_bus)

        with pytest.raises(ValidationError):
            use_case.execute(100, authorized_actor(DEPARTMENT_HEAD_ID), reason="Too expensive")

        repository.save.assert_not_called()
        event_bus.publish_all.assert_not_called()


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


class TestUpdatePurchaseRequestItems:
    """
    Tests for the UpdatePurchaseRequestItems use case (Slice 2).

    REJECTED is handled by composing correct_and_resubmit() with
    replace_items() into one atomic save - see the use case's own docstring.
    Domain-level guarantees (replace_items is DRAFT-only, correct_and_resubmit
    is REJECTED-only) are covered in tests/test_entities.py and are only
    exercised here at the orchestration boundary.
    """

    def _use_case(self, repository, policy, category_repository):
        return UpdatePurchaseRequestItems(repository, policy, category_repository)

    def _item(self, **overrides):
        defaults = {
            "description": "Keyboard",
            "quantity": 1,
            "expected_delivery_period": "2 weeks",
            "estimated_cost": Decimal("50.00"),
            "category_id": 1,
        }
        defaults.update(overrides)
        return UpdatePurchaseRequestItemDTO(**defaults)

    def test_updates_an_existing_items_fields(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item
        # draft_request_with_item's item is never persisted through a real
        # repository, so it has no id of its own yet - assign one explicitly
        # so "matching by id" is actually exercised, not vacuously true.
        draft_request_with_item.items[0]._id = 42
        existing_id = 42

        result = self._use_case(repository, policy, category_repository).execute(
            100,
            [self._item(id=existing_id, description="Updated Laptop", quantity=2)],
            requester,
        )

        assert len(result.items) == 1
        assert result.items[0].id == existing_id
        assert result.items[0].description == "Updated Laptop"
        assert result.items[0].quantity == 2
        assert result.items[0].budget_code_id == 77  # category #1 -> account 77
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_adds_a_new_item_alongside_the_existing_one(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item
        draft_request_with_item.items[0]._id = 42
        existing_id = 42

        result = self._use_case(repository, policy, category_repository).execute(
            100,
            [
                self._item(id=existing_id),
                self._item(description="Mouse"),  # no id -> new item
            ],
            requester,
        )

        assert len(result.items) == 2
        descriptions = {item.description for item in result.items}
        assert descriptions == {"Keyboard", "Mouse"}

    def test_omitting_an_existing_item_removes_it(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item

        result = self._use_case(repository, policy, category_repository).execute(
            100,
            [self._item(description="Replacement item, no id")],
            requester,
        )

        assert len(result.items) == 1
        assert result.items[0].description == "Replacement item, no id"

    def test_unknown_category_raises_and_saves_nothing(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100, [self._item(category_id=999)], requester
            )

        assert exc.value.code == "CATEGORY_NOT_FOUND"
        repository.save.assert_not_called()

    def test_inactive_category_raises_and_saves_nothing(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100, [self._item(category_id=2)], requester
            )

        assert exc.value.code == "CATEGORY_INACTIVE"
        repository.save.assert_not_called()

    def test_item_id_not_belonging_to_the_request_raises(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100, [self._item(id=999999)], requester
            )

        assert exc.value.code == "ITEM_NOT_FOUND"
        repository.save.assert_not_called()

    def test_duplicate_item_id_in_the_same_payload_raises(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item
        draft_request_with_item.items[0]._id = 42
        existing_id = 42

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100,
                [self._item(id=existing_id), self._item(id=existing_id, description="Other")],
                requester,
            )

        assert exc.value.code == "DUPLICATE_ITEM_ID"
        repository.save.assert_not_called()

    def test_not_found_raises(self, repository, policy, category_repository, requester):
        repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            self._use_case(repository, policy, category_repository).execute(
                999, [self._item()], requester
            )
        repository.save.assert_not_called()

    def test_editing_a_pending_request_is_blocked(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100, [self._item()], requester
            )

        assert exc.value.code == "REQUEST_NOT_EDITABLE"
        assert draft_request_with_item.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_editing_a_rejected_request_transitions_it_to_draft(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        draft_request_with_item.submit()
        draft_request_with_item.reject(actor_id=25, reason="Wrong budget code")
        repository.get_by_id.return_value = draft_request_with_item

        result = self._use_case(repository, policy, category_repository).execute(
            100, [self._item(description="Corrected item")], requester
        )

        assert result.status == RequestStatus.DRAFT
        assert result.items[0].description == "Corrected item"
        # The rejection decision is preserved, not erased by the correction.
        assert any(d.decision.value == "REJECTED" for d in result.decisions)
        repository.save.assert_called_once_with(draft_request_with_item)

    def test_a_failed_edit_leaves_a_rejected_request_exactly_as_rejected(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        """
        The atomicity guarantee: items are validated/resolved *before*
        correct_and_resubmit() or replace_items() is ever called, so an
        invalid edit never leaves a REJECTED request silently demoted to an
        unflagged DRAFT with nothing actually corrected.
        """
        draft_request_with_item.submit()
        draft_request_with_item.reject(actor_id=25, reason="Wrong budget code")
        repository.get_by_id.return_value = draft_request_with_item
        original_description = draft_request_with_item.items[0].description

        with pytest.raises(ValidationError) as exc:
            self._use_case(repository, policy, category_repository).execute(
                100, [self._item(category_id=999)], requester
            )

        assert exc.value.code == "CATEGORY_NOT_FOUND"
        assert draft_request_with_item.status == RequestStatus.REJECTED
        assert draft_request_with_item.items[0].description == original_description
        repository.save.assert_not_called()

    def test_description_does_not_influence_category_resolution(
        self, repository, policy, category_repository, requester, draft_request_with_item
    ):
        repository.get_by_id.return_value = draft_request_with_item

        result = self._use_case(repository, policy, category_repository).execute(
            100,
            [self._item(category_id=1, description="Unrelated text about fuel and travel")],
            requester,
        )

        assert result.items[0].budget_code_id == 77


class TestDeletePurchaseRequest:
    """
    Tests for the DeletePurchaseRequest use case (Slice 4).

    Who is allowed to delete is covered in tests/application/authorization/
    (see TestDeleteAuthorization); these cover the use case's own business
    rules - which requests are actually deletable once authorization passes.
    """

    def test_deletes_a_clean_draft(self, repository, policy, draft_request_with_item):
        repository.get_by_id.return_value = draft_request_with_item
        repository.delete.return_value = True
        use_case = DeletePurchaseRequest(repository, policy)

        result = use_case.execute(100, authorized_actor(REQUESTER_ID))

        assert result is None
        repository.delete.assert_called_once_with(100)

    def test_not_found_raises(self, repository, policy):
        repository.get_by_id.return_value = None
        use_case = DeletePurchaseRequest(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(999, authorized_actor(REQUESTER_ID))
        repository.delete.assert_not_called()

    def test_non_draft_request_raises(self, repository, policy, draft_request_with_item):
        """A submitted (PENDING_*) or PROCESSED request can never be deleted."""
        draft_request_with_item.submit()
        repository.get_by_id.return_value = draft_request_with_item
        use_case = DeletePurchaseRequest(repository, policy)

        with pytest.raises(ValidationError) as exc:
            use_case.execute(100, authorized_actor(REQUESTER_ID))

        assert exc.value.code == "NOT_DELETABLE"
        repository.delete.assert_not_called()

    def test_draft_with_decision_history_raises(
        self, repository, policy, draft_request_with_item
    ):
        """
        A rejected-then-corrected request is DRAFT again but must not be
        deletable: correct_and_resubmit() never clears request.decisions, and
        the persistence layer cascade-deletes them along with the request,
        which would silently destroy the approval/rejection audit trail.
        """
        draft_request_with_item.submit()
        draft_request_with_item.reject(DEPARTMENT_HEAD_ID, "Budget constraints")
        draft_request_with_item.correct_and_resubmit()
        assert draft_request_with_item.status == RequestStatus.DRAFT
        assert len(draft_request_with_item.decisions) == 1
        repository.get_by_id.return_value = draft_request_with_item
        use_case = DeletePurchaseRequest(repository, policy)

        with pytest.raises(ValidationError) as exc:
            use_case.execute(100, authorized_actor(REQUESTER_ID))

        assert exc.value.code == "HAS_DECISION_HISTORY"
        repository.delete.assert_not_called()

    def test_repository_returning_false_raises_not_found(
        self, repository, policy, draft_request_with_item
    ):
        """Guards a race between load and delete (e.g. the request stopped being a draft in between)."""
        repository.get_by_id.return_value = draft_request_with_item
        repository.delete.return_value = False
        use_case = DeletePurchaseRequest(repository, policy)

        with pytest.raises(NotFoundError):
            use_case.execute(100, authorized_actor(REQUESTER_ID))

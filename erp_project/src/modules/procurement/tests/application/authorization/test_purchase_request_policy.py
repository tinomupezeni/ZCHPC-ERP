"""
Authorization tests for the Purchase Request workflow.

These answer one question: who is allowed to invoke which Purchase Request
operation? Domain state-transition rules are covered by the Slice 2 tests and
are not repeated here, except where a test proves that authorization does not
replace domain validation.

Follows existing project conventions:
- class-based test organization (TestXxx)
- pytest fixtures for shared setup
- Mock repository injected via constructor
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal

from shared.domain.exceptions import AuthorizationError, NotFoundError, ValidationError
from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
    PurchaseRequestPermissions as P,
)
from modules.procurement.application.use_cases import (
    CreatePurchaseRequest,
    CreatePurchaseRequestDTO,
    PurchaseRequestItemDTO,
    ViewPurchaseRequest,
    SubmitPurchaseRequest,
    ApprovePurchaseRequestByDepartmentHead,
    VerifyPurchaseRequestByAccounts,
    RecommendPurchaseRequestByGM,
    ApprovePurchaseRequestByDirector,
    ProcessPurchaseRequestByProcurement,
    RejectPurchaseRequest,
    CorrectAndResubmitPurchaseRequest,
)


# Organizational fixture used throughout:
#   IT department (id 10)      - head #2, requester #1, non-head colleague #6
#   Finance department (id 20) - head #3
REQUESTER_ID = 1
IT_HEAD_ID = 2
FINANCE_HEAD_ID = 3
IT_COLLEAGUE_ID = 6
IT_DEPARTMENT_ID = 10
FINANCE_DEPARTMENT_ID = 20


def make_actor(employee_id, permissions, department_id=None, **kwargs):
    """Build an actor holding exactly the listed permissions."""
    return Actor(
        employee_id=employee_id,
        permissions=PermissionSet.from_list(permissions),
        department_id=department_id,
        **kwargs,
    )


def make_request(status=RequestStatus.DRAFT, requester_id=REQUESTER_ID):
    """A persisted purchase request with one item, in the given status."""
    req = PurchaseRequest.create(
        requester_id=requester_id,
        requester_name="John Doe",
        department_id=IT_DEPARTMENT_ID,
        department_name="IT",
        designation="Developer",
        contact="ext 123",
    )
    req._id = 100
    req.add_item(
        PurchaseRequestItem(
            description="Laptop",
            quantity=1,
            expected_delivery_period="2 weeks",
            estimated_cost=Decimal("1500.00"),
            budget_code_id=5,
        )
    )
    req.status = status
    return req


class StubDirectory:
    """Stub organizational directory recording each department's head."""

    def __init__(self, heads=None, departments=None):
        self.heads = heads or {}
        self.departments = departments or {}

    def get_department_head_id(self, department_id):
        return self.heads.get(department_id)

    def get_department_id(self, employee_id):
        return self.departments.get(employee_id)


@pytest.fixture
def repository():
    repo = Mock()
    repo.save.side_effect = lambda x: x
    return repo


@pytest.fixture
def directory():
    """#2 heads IT, #3 heads Finance; #1 and #6 are ordinary IT staff."""
    return StubDirectory(
        heads={IT_DEPARTMENT_ID: IT_HEAD_ID, FINANCE_DEPARTMENT_ID: FINANCE_HEAD_ID},
        departments={
            REQUESTER_ID: IT_DEPARTMENT_ID,
            IT_HEAD_ID: IT_DEPARTMENT_ID,
            IT_COLLEAGUE_ID: IT_DEPARTMENT_ID,
            FINANCE_HEAD_ID: FINANCE_DEPARTMENT_ID,
        },
    )


@pytest.fixture
def policy(directory):
    return PurchaseRequestAuthorizationPolicy(directory=directory)


# =============================================================================
# Authentication gate
# =============================================================================


class TestUnauthenticatedActor:
    """An unauthenticated actor cannot perform any protected operation."""

    @pytest.mark.parametrize(
        "use_case_cls,args",
        [
            (ViewPurchaseRequest, (100,)),
            (SubmitPurchaseRequest, (100,)),
            (ApprovePurchaseRequestByDepartmentHead, (100,)),
            (VerifyPurchaseRequestByAccounts, (100,)),
            (RecommendPurchaseRequestByGM, (100,)),
            (ApprovePurchaseRequestByDirector, (100,)),
            (ProcessPurchaseRequestByProcurement, (100,)),
            (CorrectAndResubmitPurchaseRequest, (100,)),
        ],
    )
    def test_anonymous_actor_is_denied(self, repository, policy, use_case_cls, args):
        use_case = use_case_cls(repository, policy)

        with pytest.raises(AuthorizationError) as exc:
            use_case.execute(*args, Actor.anonymous())

        assert exc.value.code == "UNAUTHENTICATED"
        repository.save.assert_not_called()

    def test_anonymous_reject_is_denied(self, repository, policy):
        use_case = RejectPurchaseRequest(repository, policy)

        with pytest.raises(AuthorizationError):
            use_case.execute(100, Actor.anonymous(), "no budget")

        repository.save.assert_not_called()

    def test_anonymous_create_is_denied(self, repository, policy):
        use_case = CreatePurchaseRequest(repository, policy)
        dto = CreatePurchaseRequestDTO(
            requester_id=REQUESTER_ID,
            requester_name="John Doe",
            department_id=IT_DEPARTMENT_ID,
            department_name="IT",
            designation="Developer",
            contact="ext 123",
        )

        with pytest.raises(AuthorizationError):
            use_case.execute(dto, Actor.anonymous())

        repository.save.assert_not_called()

    def test_none_actor_is_denied(self, repository, policy):
        use_case = SubmitPurchaseRequest(repository, policy)

        with pytest.raises(AuthorizationError):
            use_case.execute(100, None)

        repository.save.assert_not_called()

    def test_existence_is_not_disclosed_before_authentication(self, repository, policy):
        """An anonymous caller gets denied, not told the request is missing."""
        repository.get_by_id.return_value = None
        use_case = SubmitPurchaseRequest(repository, policy)

        with pytest.raises(AuthorizationError):
            use_case.execute(999, Actor.anonymous())

        repository.get_by_id.assert_not_called()


# =============================================================================
# Create
# =============================================================================


class TestCreateAuthorization:
    @pytest.fixture
    def dto(self):
        return CreatePurchaseRequestDTO(
            requester_id=REQUESTER_ID,
            requester_name="John Doe",
            department_id=IT_DEPARTMENT_ID,
            department_name="IT",
            designation="Developer",
            contact="ext 123",
            items=[
                PurchaseRequestItemDTO(
                    description="Laptop",
                    quantity=1,
                    expected_delivery_period="2 weeks",
                    estimated_cost=Decimal("1500.00"),
                    budget_code_id=5,
                )
            ],
        )

    def test_actor_without_create_permission_is_denied(self, repository, policy, dto):
        actor = make_actor(REQUESTER_ID, [P.VIEW], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            CreatePurchaseRequest(repository, policy).execute(dto, actor)

        assert exc.value.code == "PERMISSION_DENIED"
        repository.save.assert_not_called()

    def test_actor_with_create_permission_is_allowed(self, repository, policy, dto):
        actor = make_actor(REQUESTER_ID, [P.CREATE], IT_DEPARTMENT_ID)

        result = CreatePurchaseRequest(repository, policy).execute(dto, actor)

        assert result.requester_id == REQUESTER_ID
        repository.save.assert_called_once()

    def test_cannot_raise_a_request_in_somebody_elses_name(
        self, repository, policy, dto
    ):
        actor = make_actor(2, [P.CREATE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            CreatePurchaseRequest(repository, policy).execute(dto, actor)

        assert exc.value.code == "REQUESTER_MISMATCH"
        repository.save.assert_not_called()


# =============================================================================
# View
# =============================================================================


class TestViewAuthorization:
    def test_actor_without_view_permission_is_denied(self, repository, policy):
        repository.get_by_id.return_value = make_request()
        actor = make_actor(REQUESTER_ID, [P.CREATE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ViewPurchaseRequest(repository, policy).execute(100, actor)

        assert exc.value.code == "PERMISSION_DENIED"

    def test_actor_with_view_permission_is_allowed(self, repository, policy):
        request = make_request()
        repository.get_by_id.return_value = request
        actor = make_actor(REQUESTER_ID, [P.VIEW], IT_DEPARTMENT_ID)

        assert ViewPurchaseRequest(repository, policy).execute(100, actor) is request

    def test_view_does_not_mutate_or_save(self, repository, policy):
        repository.get_by_id.return_value = make_request()
        actor = make_actor(REQUESTER_ID, [P.VIEW], IT_DEPARTMENT_ID)

        ViewPurchaseRequest(repository, policy).execute(100, actor)

        repository.save.assert_not_called()


# =============================================================================
# Submit
# =============================================================================


class TestSubmitAuthorization:
    def test_actor_without_submit_permission_is_denied(self, repository, policy):
        repository.get_by_id.return_value = make_request()
        actor = make_actor(REQUESTER_ID, [P.VIEW], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            SubmitPurchaseRequest(repository, policy).execute(100, actor)

        assert exc.value.code == "PERMISSION_DENIED"
        repository.save.assert_not_called()

    def test_requester_with_submit_permission_is_allowed(self, repository, policy):
        repository.get_by_id.return_value = make_request()
        actor = make_actor(REQUESTER_ID, [P.SUBMIT], IT_DEPARTMENT_ID)

        result = SubmitPurchaseRequest(repository, policy).execute(100, actor)

        assert result.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_called_once()

    def test_another_employee_cannot_submit_someone_elses_request(
        self, repository, policy
    ):
        repository.get_by_id.return_value = make_request()
        actor = make_actor(2, [P.SUBMIT], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            SubmitPurchaseRequest(repository, policy).execute(100, actor)

        assert exc.value.code == "NOT_REQUESTER"
        repository.save.assert_not_called()


# =============================================================================
# Department head approval - business context
# =============================================================================


class TestDepartmentHeadAuthorization:
    """
    Authority comes from the authoritative relationship only:

        PurchaseRequest.department -> Department.head -> Employees
    """

    @pytest.fixture
    def pending(self, repository):
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        repository.get_by_id.return_value = request
        return request

    def test_actor_without_permission_is_denied(self, repository, policy, pending):
        actor = make_actor(IT_HEAD_ID, [P.VIEW], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        assert exc.value.code == "PERMISSION_DENIED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_recorded_head_of_the_requests_department_is_allowed(
        self, repository, policy, pending
    ):
        actor = make_actor(IT_HEAD_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        result = ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(
            100, actor
        )

        assert result is pending
        assert result.status == RequestStatus.PENDING_ACCOUNTS
        repository.save.assert_called_once()

    def test_member_of_the_department_who_is_not_the_head_is_denied(
        self, repository, policy, pending
    ):
        """Department membership alone is not authority."""
        actor = make_actor(
            IT_COLLEAGUE_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID
        )

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_head_of_another_department_is_denied(self, repository, policy, pending):
        """Holding the capability does not authorize acting on every department."""
        actor = make_actor(
            FINANCE_HEAD_ID, [P.DEPARTMENT_HEAD_APPROVE], FINANCE_DEPARTMENT_ID
        )

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_authority_does_not_depend_on_the_actors_own_department(
        self, repository, pending
    ):
        """
        The head relationship is what counts - a head recorded for IT while
        sitting in another department is still IT's authority.
        """
        directory = StubDirectory(
            heads={IT_DEPARTMENT_ID: 4},
            departments={4: FINANCE_DEPARTMENT_ID},
        )
        scoped_policy = PurchaseRequestAuthorizationPolicy(directory=directory)
        actor = make_actor(4, [P.DEPARTMENT_HEAD_APPROVE], FINANCE_DEPARTMENT_ID)

        result = ApprovePurchaseRequestByDepartmentHead(repository, scoped_policy).execute(
            100, actor
        )

        assert result is pending
        assert result.status == RequestStatus.PENDING_ACCOUNTS

    def test_department_with_no_recorded_head_denies_everyone(
        self, repository, pending
    ):
        """Fails closed rather than falling back to department membership."""
        directory = StubDirectory(
            heads={}, departments={IT_HEAD_ID: IT_DEPARTMENT_ID}
        )
        scoped_policy = PurchaseRequestAuthorizationPolicy(directory=directory)
        actor = make_actor(IT_HEAD_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, scoped_policy).execute(
                100, actor
            )

        assert exc.value.code == "DEPARTMENT_HEAD_NOT_RECORDED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_policy_without_a_directory_denies_department_approval(
        self, repository, pending
    ):
        """Fails closed when no organizational directory is wired in."""
        blind_policy = PurchaseRequestAuthorizationPolicy()
        actor = make_actor(IT_HEAD_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, blind_policy).execute(
                100, actor
            )

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_head_who_raised_the_request_cannot_approve_it(
        self, repository, pending
    ):
        """Self-approval stays denied even for the department's own head."""
        directory = StubDirectory(
            heads={IT_DEPARTMENT_ID: REQUESTER_ID},
            departments={REQUESTER_ID: IT_DEPARTMENT_ID},
        )
        scoped_policy = PurchaseRequestAuthorizationPolicy(directory=directory)
        actor = make_actor(REQUESTER_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, scoped_policy).execute(
                100, actor
            )

        assert exc.value.code == "SELF_APPROVAL_FORBIDDEN"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_requester_cannot_approve_their_own_request(
        self, repository, policy, pending
    ):
        actor = make_actor(REQUESTER_ID, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"
        assert pending.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        repository.save.assert_not_called()

    def test_admin_bypasses_department_context_but_not_self_approval(
        self, repository, policy, pending
    ):
        admin_other = Actor(
            employee_id=9,
            permissions=PermissionSet.empty(),
            role_name="SYSTEM_ADMINISTRATOR",
        )
        ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(
            100, admin_other
        )
        assert pending.status == RequestStatus.PENDING_ACCOUNTS

        pending.status = RequestStatus.PENDING_DEPARTMENT_HEAD
        admin_requester = Actor(
            employee_id=REQUESTER_ID,
            permissions=PermissionSet.empty(),
            role_name="SYSTEM_ADMINISTRATOR",
        )
        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(
                100, admin_requester
            )
        assert exc.value.code == "SELF_APPROVAL_FORBIDDEN"


# =============================================================================
# Organization-wide offices: Accounts, GM, Director, Procurement
# =============================================================================


class TestWorkflowOfficeAuthorization:
    """
    Accounts, GM, Director and Procurement are single organization-wide
    offices, so the capability itself carries the authority. The only
    contextual constraint the model supports is the self-approval prohibition.
    """

    @pytest.mark.parametrize(
        "use_case_cls,status,permission,next_status",
        [
            (
                VerifyPurchaseRequestByAccounts,
                RequestStatus.PENDING_ACCOUNTS,
                P.ACCOUNTS_VERIFY,
                RequestStatus.PENDING_GM,
            ),
            (
                RecommendPurchaseRequestByGM,
                RequestStatus.PENDING_GM,
                P.GM_RECOMMEND,
                RequestStatus.PENDING_DIRECTOR,
            ),
            (
                ApprovePurchaseRequestByDirector,
                RequestStatus.PENDING_DIRECTOR,
                P.DIRECTOR_APPROVE,
                RequestStatus.PENDING_PROCUREMENT,
            ),
            (
                ProcessPurchaseRequestByProcurement,
                RequestStatus.PENDING_PROCUREMENT,
                P.PROCESS,
                RequestStatus.PROCESSED,
            ),
        ],
    )
    def test_permission_governs_each_office(
        self, repository, policy, use_case_cls, status, permission, next_status
    ):
        request = make_request(status)
        repository.get_by_id.return_value = request
        use_case = use_case_cls(repository, policy)

        # Wrong capability for this stage -> denied, nothing saved.
        wrong = make_actor(5, [P.VIEW, P.SUBMIT], FINANCE_DEPARTMENT_ID)
        with pytest.raises(AuthorizationError) as exc:
            use_case.execute(100, wrong)
        assert exc.value.code == "PERMISSION_DENIED"
        assert request.status == status
        repository.save.assert_not_called()

        # Correct capability -> reaches the domain method.
        holder = make_actor(5, [permission], FINANCE_DEPARTMENT_ID)
        result = use_case.execute(100, holder)
        assert result.status == next_status
        repository.save.assert_called_once()

    @pytest.mark.parametrize(
        "use_case_cls,status,permission",
        [
            (VerifyPurchaseRequestByAccounts, RequestStatus.PENDING_ACCOUNTS, P.ACCOUNTS_VERIFY),
            (RecommendPurchaseRequestByGM, RequestStatus.PENDING_GM, P.GM_RECOMMEND),
            (ApprovePurchaseRequestByDirector, RequestStatus.PENDING_DIRECTOR, P.DIRECTOR_APPROVE),
            (ProcessPurchaseRequestByProcurement, RequestStatus.PENDING_PROCUREMENT, P.PROCESS),
        ],
    )
    def test_requester_cannot_act_on_their_own_request(
        self, repository, policy, use_case_cls, status, permission
    ):
        request = make_request(status)
        repository.get_by_id.return_value = request
        actor = make_actor(REQUESTER_ID, [permission], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            use_case_cls(repository, policy).execute(100, actor)

        assert exc.value.code == "SELF_APPROVAL_FORBIDDEN"
        assert request.status == status
        repository.save.assert_not_called()

    def test_records_the_actors_employee_id_not_a_caller_supplied_id(
        self, repository, policy
    ):
        """The decision is attributed to the authenticated actor."""
        request = make_request(RequestStatus.PENDING_ACCOUNTS)
        repository.get_by_id.return_value = request
        actor = make_actor(7, [P.ACCOUNTS_VERIFY], FINANCE_DEPARTMENT_ID)

        result = VerifyPurchaseRequestByAccounts(repository, policy).execute(100, actor)

        assert result.decisions[-1].actor_id == 7


# =============================================================================
# Reject
# =============================================================================


class TestRejectAuthorization:
    def test_actor_without_reject_permission_is_denied(self, repository, policy):
        repository.get_by_id.return_value = make_request(
            RequestStatus.PENDING_DEPARTMENT_HEAD
        )
        actor = make_actor(2, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            RejectPurchaseRequest(repository, policy).execute(100, actor, "too costly")

        assert exc.value.code == "PERMISSION_DENIED"
        repository.save.assert_not_called()

    def test_stage_authority_holder_may_reject(self, repository, policy):
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        repository.get_by_id.return_value = request
        actor = make_actor(2, [P.REJECT, P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        result = RejectPurchaseRequest(repository, policy).execute(100, actor, "too costly")

        assert result.status == RequestStatus.REJECTED
        repository.save.assert_called_once()

    def test_cannot_reject_a_stage_the_actor_has_no_authority_over(
        self, repository, policy
    ):
        """Holding `reject` alone must not kill a request at another desk."""
        request = make_request(RequestStatus.PENDING_DIRECTOR)
        repository.get_by_id.return_value = request
        actor = make_actor(2, [P.REJECT, P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            RejectPurchaseRequest(repository, policy).execute(100, actor, "no")

        assert exc.value.code == "PERMISSION_DENIED"
        assert request.status == RequestStatus.PENDING_DIRECTOR
        repository.save.assert_not_called()

    def test_department_context_applies_to_rejection_too(self, repository, policy):
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        repository.get_by_id.return_value = request
        actor = make_actor(
            3, [P.REJECT, P.DEPARTMENT_HEAD_APPROVE], FINANCE_DEPARTMENT_ID
        )

        with pytest.raises(AuthorizationError) as exc:
            RejectPurchaseRequest(repository, policy).execute(100, actor, "no")

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"
        repository.save.assert_not_called()

    def test_requester_cannot_reject_their_own_request(self, repository):
        """Even the department's own head cannot reject the request they raised."""
        repository.get_by_id.return_value = make_request(
            RequestStatus.PENDING_DEPARTMENT_HEAD
        )
        directory = StubDirectory(
            heads={IT_DEPARTMENT_ID: REQUESTER_ID},
            departments={REQUESTER_ID: IT_DEPARTMENT_ID},
        )
        scoped_policy = PurchaseRequestAuthorizationPolicy(directory=directory)
        actor = make_actor(
            REQUESTER_ID, [P.REJECT, P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID
        )

        with pytest.raises(AuthorizationError) as exc:
            RejectPurchaseRequest(repository, scoped_policy).execute(
                100, actor, "changed mind"
            )

        assert exc.value.code == "SELF_APPROVAL_FORBIDDEN"
        repository.save.assert_not_called()


# =============================================================================
# Correct and resubmit
# =============================================================================


class TestCorrectAndResubmitAuthorization:
    @pytest.fixture
    def rejected(self, repository):
        request = make_request(RequestStatus.REJECTED)
        repository.get_by_id.return_value = request
        return request

    def test_requires_both_correct_and_resubmit(self, repository, policy, rejected):
        correct_only = make_actor(REQUESTER_ID, [P.CORRECT], IT_DEPARTMENT_ID)
        with pytest.raises(AuthorizationError) as exc:
            CorrectAndResubmitPurchaseRequest(repository, policy).execute(100, correct_only)
        assert exc.value.details["required_permission"] == P.RESUBMIT

        resubmit_only = make_actor(REQUESTER_ID, [P.RESUBMIT], IT_DEPARTMENT_ID)
        with pytest.raises(AuthorizationError) as exc:
            CorrectAndResubmitPurchaseRequest(repository, policy).execute(100, resubmit_only)
        assert exc.value.details["required_permission"] == P.CORRECT

        assert rejected.status == RequestStatus.REJECTED
        repository.save.assert_not_called()

    def test_requester_with_both_permissions_is_allowed(
        self, repository, policy, rejected
    ):
        actor = make_actor(REQUESTER_ID, [P.CORRECT, P.RESUBMIT], IT_DEPARTMENT_ID)

        result = CorrectAndResubmitPurchaseRequest(repository, policy).execute(100, actor)

        assert result is rejected
        assert result.status == RequestStatus.DRAFT
        repository.save.assert_called_once()

    def test_another_employee_cannot_correct_someone_elses_request(
        self, repository, policy, rejected
    ):
        actor = make_actor(2, [P.CORRECT, P.RESUBMIT], IT_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            CorrectAndResubmitPurchaseRequest(repository, policy).execute(100, actor)

        assert exc.value.code == "NOT_REQUESTER"
        assert rejected.status == RequestStatus.REJECTED
        repository.save.assert_not_called()


# =============================================================================
# Security invariants
# =============================================================================


class TestSecurityInvariants:
    def test_denied_authorization_leaves_the_aggregate_untouched(
        self, repository, policy
    ):
        """denied -> domain method not executed -> save not called -> unchanged."""
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        request.approve_by_department_head = Mock(
            side_effect=AssertionError("domain method must not be reached")
        )
        repository.get_by_id.return_value = request
        actor = make_actor(3, [P.DEPARTMENT_HEAD_APPROVE], FINANCE_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError):
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        request.approve_by_department_head.assert_not_called()
        repository.save.assert_not_called()
        assert request.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        assert request.decisions == []

    def test_authorized_operation_reaches_the_domain_method(self, repository, policy):
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        request.approve_by_department_head = Mock()
        repository.get_by_id.return_value = request
        actor = make_actor(2, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        request.approve_by_department_head.assert_called_once_with(2)
        repository.save.assert_called_once()

    def test_authorization_does_not_replace_domain_validation(self, repository, policy):
        """An authorized actor still cannot force an invalid state transition."""
        request = make_request(RequestStatus.PROCESSED)
        repository.get_by_id.return_value = request
        actor = make_actor(2, [P.DEPARTMENT_HEAD_APPROVE], IT_DEPARTMENT_ID)

        with pytest.raises(ValidationError):
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(100, actor)

        assert request.status == RequestStatus.PROCESSED
        repository.save.assert_not_called()

    def test_missing_request_is_reported_to_an_authenticated_actor(
        self, repository, policy
    ):
        repository.get_by_id.return_value = None
        actor = make_actor(REQUESTER_ID, [P.SUBMIT], IT_DEPARTMENT_ID)

        with pytest.raises(NotFoundError):
            SubmitPurchaseRequest(repository, policy).execute(999, actor)

    @pytest.mark.parametrize(
        "use_case_cls,status",
        [
            (ApprovePurchaseRequestByDepartmentHead, RequestStatus.PENDING_DEPARTMENT_HEAD),
            (VerifyPurchaseRequestByAccounts, RequestStatus.PENDING_ACCOUNTS),
            (RecommendPurchaseRequestByGM, RequestStatus.PENDING_GM),
            (ApprovePurchaseRequestByDirector, RequestStatus.PENDING_DIRECTOR),
            (ProcessPurchaseRequestByProcurement, RequestStatus.PENDING_PROCUREMENT),
        ],
    )
    def test_workflow_decisions_require_an_employee_profile(
        self, repository, policy, use_case_cls, status
    ):
        """
        A decision has to be attributable. A superuser with no employee profile
        is refused here rather than writing a null actor reference.
        """
        request = make_request(status)
        repository.get_by_id.return_value = request
        faceless_admin = Actor(
            employee_id=None,
            permissions=PermissionSet.empty(),
            role_name="ADMIN",
            is_superuser=True,
        )

        with pytest.raises(AuthorizationError) as exc:
            use_case_cls(repository, policy).execute(100, faceless_admin)

        assert exc.value.code == "NO_EMPLOYEE_PROFILE"
        assert request.status == status
        repository.save.assert_not_called()

    def test_module_wildcard_grant_covers_purchase_request_capabilities(
        self, repository, policy
    ):
        """
        Documents existing Permission semantics: a role granted `procurement.*`
        holds every Purchase Request capability. Context rules still apply.
        """
        request = make_request(RequestStatus.PENDING_DEPARTMENT_HEAD)
        repository.get_by_id.return_value = request
        wildcard_other_department = make_actor(3, ["procurement.*"], FINANCE_DEPARTMENT_ID)

        with pytest.raises(AuthorizationError) as exc:
            ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(
                100, wildcard_other_department
            )

        assert exc.value.code == "DEPARTMENT_CONTEXT_DENIED"

"""
REM-03: LeaveActor and LeaveAuthorizationPolicy (no database).

Pins the shape of the decision: authentication first; own data needs no
capability for self-service operations; other employees' data needs the
matching capability; review always needs its capability; role
names play no part; and the confirmed rule that review authority is
capability-only (no organizational relationship is consulted).
"""

from dataclasses import dataclass

import pytest

from modules.identity.domain.value_objects import PermissionSet
from modules.leave.application.authorization import (
    LeaveActor,
    LeaveAuthorizationPolicy,
    LeavePermissions as L,
)
from shared.domain.exceptions import AuthorizationError

OWN = 1
OTHER = 2


def actor(*permissions, employee_id=OWN, is_superuser=False):
    return LeaveActor(
        employee_id=employee_id,
        permissions=PermissionSet.from_list(list(permissions)),
        is_superuser=is_superuser,
    )


@dataclass
class Req:
    employee_id: int


policy = LeaveAuthorizationPolicy()


def denied(call):
    with pytest.raises(AuthorizationError) as exc:
        call()
    return exc.value


class TestAuthentication:
    @pytest.mark.parametrize("call", [
        lambda a: policy.authorize_submit(a, OWN),
        lambda a: policy.authorize_view_request(a, OWN),
        lambda a: policy.authorize_view_employee_requests(a, OWN),
        lambda a: policy.authorize_cancel_request(a, OWN),
        lambda a: policy.authorize_review_request(a, OTHER),
        lambda a: policy.authorize_view_balance(a, OWN),
        lambda a: policy.authorize_manage_balance(a, OWN),
        lambda a: policy.authorize_manage_types(a),
        lambda a: policy.filter_viewable_requests(a, [Req(OWN)]),
        lambda a: policy.filter_reviewable_requests(a, [Req(OTHER)]),
    ])
    def test_anonymous_and_none_are_denied(self, call):
        assert denied(lambda: call(LeaveActor.anonymous())).code == "UNAUTHENTICATED"
        assert denied(lambda: call(None)).code == "UNAUTHENTICATED"

    def test_anonymous_with_superuser_flag_is_still_denied(self):
        a = LeaveActor(is_superuser=True, is_authenticated=False, employee_id=OWN)
        denied(lambda: policy.authorize_view_request(a, OWN))


class TestOwnDataSelfService:
    def test_own_request_view_cancel_and_list_need_no_capability(self):
        a = actor()
        policy.authorize_view_request(a, OWN)
        policy.authorize_cancel_request(a, OWN)
        policy.authorize_view_employee_requests(a, OWN)
        policy.authorize_view_balance(a, OWN)
        policy.authorize_submit(a, OWN)

    def test_other_employee_is_denied_without_capability(self):
        a = actor()
        for call in (
            lambda: policy.authorize_view_request(a, OTHER),
            lambda: policy.authorize_cancel_request(a, OTHER),
            lambda: policy.authorize_view_employee_requests(a, OTHER),
            lambda: policy.authorize_view_balance(a, OTHER),
        ):
            assert denied(call).code == "LEAVE_PERMISSION_DENIED"

    def test_unresolved_target_is_denied_without_capability(self):
        """Missing records look the same as other people's records."""
        denied(lambda: policy.authorize_view_request(actor(), None))
        denied(lambda: policy.authorize_cancel_request(actor(), None))
        denied(lambda: policy.authorize_view_balance(actor(), None))

    def test_unlinked_actor_owns_nothing(self):
        a = actor(employee_id=None)
        denied(lambda: policy.authorize_view_request(a, None))
        denied(lambda: policy.authorize_submit(a, OWN))

    def test_submit_is_own_only_even_for_full_access(self):
        assert denied(lambda: policy.authorize_submit(actor("*"), OTHER)).code == "LEAVE_SUBMIT_NOT_OWN"
        denied(lambda: policy.authorize_submit(actor(is_superuser=True), OTHER))


class TestCapabilities:
    @pytest.mark.parametrize("call, capability", [
        (lambda a: policy.authorize_view_request(a, OTHER), L.REQUEST_VIEW_ANY),
        (lambda a: policy.authorize_cancel_request(a, OTHER), L.REQUEST_CANCEL_ANY),
        (lambda a: policy.authorize_review_request(a, OTHER), L.REQUEST_REVIEW),
        (lambda a: policy.authorize_view_balance(a, OTHER), L.BALANCE_VIEW_ANY),
        (lambda a: policy.authorize_manage_balance(a, OTHER), L.BALANCE_MANAGE),
        (lambda a: policy.authorize_manage_types(a), L.TYPE_MANAGE),
    ])
    def test_each_operation_needs_exactly_its_capability(self, call, capability):
        call(actor(capability))
        others = [c for c in vars(L).values() if isinstance(c, str) and c.startswith("leave.") and c != capability]
        err = denied(lambda: call(actor(*others)))
        assert err.details["required_permission"] == capability

    def test_review_needs_capability_even_on_own_request(self):
        denied(lambda: policy.authorize_review_request(actor(), OWN))

    def test_balance_management_needs_capability_even_for_own_balance(self):
        denied(lambda: policy.authorize_manage_balance(actor(L.BALANCE_VIEW_ANY), OWN))

    def test_view_any_does_not_imply_cancel_or_review(self):
        a = actor(L.REQUEST_VIEW_ANY)
        denied(lambda: policy.authorize_cancel_request(a, OTHER))
        denied(lambda: policy.authorize_review_request(a, OTHER))

    def test_wildcards_and_superuser_are_preserved(self):
        for a in (actor("leave.*"), actor("*"), actor(employee_id=None, is_superuser=True)):
            policy.authorize_review_request(a, OTHER)
            policy.authorize_manage_balance(a, OTHER)
            policy.authorize_manage_types(a)
            policy.authorize_view_request(a, None)

    def test_other_module_wildcards_grant_nothing(self):
        denied(lambda: policy.authorize_review_request(actor("hr.*", "payroll.*"), OTHER))


class TestRoleNamesAndRelationshipsAreNotPolicy:
    def test_actor_has_no_role_or_org_fields(self):
        a = actor()
        for attr in ("role_name", "department_id", "reports_to_id"):
            assert not hasattr(a, attr)

    def test_review_does_not_depend_on_target_identity(self):
        a = actor(L.REQUEST_REVIEW)
        for target in (2, 3, 999):
            policy.authorize_review_request(a, target)


class TestListFiltering:
    requests = [Req(OWN), Req(OTHER), Req(3)]

    def test_ordinary_employee_sees_only_own(self):
        assert [r.employee_id for r in policy.filter_viewable_requests(actor(), self.requests)] == [OWN]

    def test_view_any_sees_everything(self):
        assert len(policy.filter_viewable_requests(actor(L.REQUEST_VIEW_ANY), self.requests)) == 3

    def test_review_queue_is_empty_without_capability(self):
        assert policy.filter_reviewable_requests(actor(L.REQUEST_VIEW_ANY), self.requests) == []

    def test_review_queue_excludes_own_requests(self):
        rows = policy.filter_reviewable_requests(actor(L.REQUEST_REVIEW), self.requests)
        assert [r.employee_id for r in rows] == [OTHER, 3]

    def test_filters_consult_the_target_hook_per_record(self):
        class NotThree(LeaveAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                return target_employee_id != 3

        p = NotThree()
        assert [r.employee_id for r in p.filter_viewable_requests(actor(L.REQUEST_VIEW_ANY), self.requests)] == [OWN, OTHER]
        assert [r.employee_id for r in p.filter_reviewable_requests(actor(L.REQUEST_REVIEW), self.requests)] == [OTHER]

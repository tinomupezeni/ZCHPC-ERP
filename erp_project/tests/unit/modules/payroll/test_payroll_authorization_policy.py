"""
REM-02 Slice A: PayrollActor and PayrollAuthorizationPolicy.

Pure unit tests (no database). Capability names come from
PayrollPermissions so that a later rename does not touch these tests; what
is being pinned is the *shape* of the decision:

- authentication is required;
- the capability must be held, via real PermissionSet semantics;
- role names never matter;
- the policy is target-aware (the hook receives the target employee) even
  though the current minimal semantics grant a capability for every target;
- list filtering is a per-record decision, not just a route decision.
"""

from dataclasses import dataclass

import pytest

from modules.identity.domain.value_objects import PermissionSet
from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
    PayrollPermissions,
    PayslipTarget,
)
from shared.domain.exceptions import AuthorizationError


def actor_with(*permissions, employee_id=1, is_superuser=False):
    return PayrollActor(
        employee_id=employee_id,
        permissions=PermissionSet.from_list(list(permissions)),
        is_superuser=is_superuser,
    )


@dataclass
class FakePayslip:
    employee_id: int


class TestAuthenticationGate:
    def test_anonymous_actor_is_denied_every_operation(self):
        policy = PayrollAuthorizationPolicy()
        anonymous = PayrollActor.anonymous()
        calls = [
            lambda: policy.authorize_view_payslip(anonymous, FakePayslip(2)),
            lambda: policy.authorize_list_payslips(anonymous),
            lambda: policy.authorize_process_payroll(anonymous),
            lambda: policy.authorize_approve_payslip(anonymous, FakePayslip(2)),
            lambda: policy.authorize_view_payroll_profile(anonymous, 2),
            lambda: policy.authorize_manage_payroll_profile(anonymous, 2),
            lambda: policy.authorize_view_statutory_profile(anonymous, 2),
            lambda: policy.authorize_manage_statutory_profile(anonymous, 2),
            lambda: policy.authorize_view_bank_accounts(anonymous, 2),
            lambda: policy.authorize_manage_bank_accounts(anonymous, 2),
            lambda: policy.authorize_view_summary(anonymous),
            lambda: policy.authorize_view_configuration(anonymous),
            lambda: policy.authorize_manage_configuration(anonymous),
        ]
        for call in calls:
            with pytest.raises(AuthorizationError) as exc_info:
                call()
            assert exc_info.value.code == "UNAUTHENTICATED"

    def test_none_actor_is_denied(self):
        with pytest.raises(AuthorizationError):
            PayrollAuthorizationPolicy().authorize_view_summary(None)

    def test_anonymous_actor_is_denied_even_if_it_somehow_carries_full_access(self):
        actor = PayrollActor(
            permissions=PermissionSet.full_access(),
            is_superuser=True,
            is_authenticated=False,
        )
        with pytest.raises(AuthorizationError):
            PayrollAuthorizationPolicy().authorize_view_summary(actor)


class TestCapabilityGate:
    @pytest.mark.parametrize(
        "method, args, capability",
        [
            ("authorize_view_payslip", (FakePayslip(2),), PayrollPermissions.PAYSLIP_VIEW),
            ("authorize_list_payslips", (), PayrollPermissions.PAYSLIP_VIEW),
            ("authorize_process_payroll", (), PayrollPermissions.PAYSLIP_PROCESS),
            ("authorize_approve_payslip", (FakePayslip(2),), PayrollPermissions.PAYSLIP_APPROVE),
            ("authorize_view_payroll_profile", (2,), PayrollPermissions.PROFILE_VIEW),
            ("authorize_manage_payroll_profile", (2,), PayrollPermissions.PROFILE_MANAGE),
            ("authorize_view_statutory_profile", (2,), PayrollPermissions.STATUTORY_VIEW),
            ("authorize_manage_statutory_profile", (2,), PayrollPermissions.STATUTORY_MANAGE),
            ("authorize_view_bank_accounts", (2,), PayrollPermissions.BANK_VIEW),
            ("authorize_manage_bank_accounts", (2,), PayrollPermissions.BANK_MANAGE),
            ("authorize_view_summary", (), PayrollPermissions.SUMMARY_VIEW),
            ("authorize_view_configuration", (), PayrollPermissions.CONFIG_VIEW),
            ("authorize_manage_configuration", (), PayrollPermissions.CONFIG_MANAGE),
        ],
    )
    def test_each_operation_needs_exactly_its_capability(self, method, args, capability):
        policy = PayrollAuthorizationPolicy()

        getattr(policy, method)(actor_with(capability), *args)  # allowed

        with pytest.raises(AuthorizationError) as exc_info:
            getattr(policy, method)(actor_with(), *args)
        assert exc_info.value.code == "PAYROLL_PERMISSION_DENIED"
        assert exc_info.value.details["required_permission"] == capability

    def test_a_different_payroll_capability_is_not_enough(self):
        policy = PayrollAuthorizationPolicy()
        with pytest.raises(AuthorizationError):
            policy.authorize_view_bank_accounts(
                actor_with(PayrollPermissions.PROFILE_VIEW, PayrollPermissions.STATUTORY_VIEW), 2
            )

    def test_view_and_manage_are_distinct(self):
        policy = PayrollAuthorizationPolicy()
        with pytest.raises(AuthorizationError):
            policy.authorize_manage_payroll_profile(actor_with(PayrollPermissions.PROFILE_VIEW), 2)

    def test_approval_is_not_inherited_from_process_or_view(self):
        policy = PayrollAuthorizationPolicy()
        actor = actor_with(
            PayrollPermissions.PAYSLIP_VIEW,
            PayrollPermissions.PAYSLIP_PROCESS,
            PayrollPermissions.CONFIG_MANAGE,
        )
        with pytest.raises(AuthorizationError):
            policy.authorize_approve_payslip(actor, FakePayslip(2))

    def test_capability_from_another_module_is_not_enough(self):
        policy = PayrollAuthorizationPolicy()
        with pytest.raises(AuthorizationError):
            policy.authorize_view_summary(actor_with("hr.*", "procurement.*"))

    def test_existing_payroll_wildcard_semantics_are_preserved(self):
        policy = PayrollAuthorizationPolicy()
        policy.authorize_approve_payslip(actor_with("payroll.*"), FakePayslip(2))
        policy.authorize_manage_configuration(actor_with("*"))

    def test_superuser_flag_alone_is_sufficient(self):
        policy = PayrollAuthorizationPolicy()
        superuser = PayrollActor(employee_id=None, permissions=PermissionSet.empty(), is_superuser=True)
        policy.authorize_approve_payslip(superuser, FakePayslip(2))
        policy.authorize_manage_bank_accounts(superuser, 2)


class TestRoleNamesAreNotPolicy:
    def test_actor_carries_no_role_name(self):
        assert not hasattr(actor_with(), "role_name")

    def test_decision_depends_only_on_permissions(self):
        # Two actors with identical permissions get identical decisions;
        # nothing else about them (there is no role field) can differ.
        policy = PayrollAuthorizationPolicy()
        a = actor_with(PayrollPermissions.PAYSLIP_VIEW, employee_id=1)
        b = actor_with(PayrollPermissions.PAYSLIP_VIEW, employee_id=99)
        policy.authorize_view_payslip(a, FakePayslip(5))
        policy.authorize_view_payslip(b, FakePayslip(5))


class TestActorVersusTargetIsEvaluated:
    def test_target_is_passed_to_the_target_decision_hook(self):
        seen = []

        class RecordingPolicy(PayrollAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                seen.append((capability, target_employee_id))
                return True

        policy = RecordingPolicy()
        actor = actor_with(PayrollPermissions.PAYSLIP_VIEW, PayrollPermissions.BANK_MANAGE, employee_id=1)
        policy.authorize_view_payslip(actor, FakePayslip(42))
        policy.authorize_manage_bank_accounts(actor, 43)

        assert (PayrollPermissions.PAYSLIP_VIEW, 42) in seen
        assert (PayrollPermissions.BANK_MANAGE, 43) in seen

    def test_a_narrowing_policy_can_deny_by_target_without_touching_callers(self):
        class OwnRecordOnly(PayrollAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                return target_employee_id == actor.employee_id

        policy = OwnRecordOnly()
        actor = actor_with(PayrollPermissions.PAYSLIP_VIEW, PayrollPermissions.PROFILE_VIEW, employee_id=1)

        policy.authorize_view_payslip(actor, FakePayslip(1))
        with pytest.raises(AuthorizationError) as exc_info:
            policy.authorize_view_payslip(actor, FakePayslip(2))
        assert exc_info.value.code == "PAYROLL_TARGET_DENIED"
        with pytest.raises(AuthorizationError):
            policy.authorize_view_payroll_profile(actor, 2)

    def test_unresolved_target_is_evaluated_as_target_none(self):
        seen = []

        class RecordingPolicy(PayrollAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                seen.append(target_employee_id)
                return True

        RecordingPolicy().authorize_view_payslip(actor_with(PayrollPermissions.PAYSLIP_VIEW), None)
        assert seen == [None]


class TestListFiltering:
    def test_filter_returns_only_records_the_actor_may_view(self):
        class EvenEmployeesOnly(PayrollAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                return target_employee_id % 2 == 0

        payslips = [FakePayslip(i) for i in range(1, 7)]
        actor = actor_with(PayrollPermissions.PAYSLIP_VIEW)

        visible = EvenEmployeesOnly().filter_viewable_payslips(actor, payslips)

        assert [p.employee_id for p in visible] == [2, 4, 6]

    def test_filter_without_the_capability_raises_rather_than_returning_everything(self):
        with pytest.raises(AuthorizationError):
            PayrollAuthorizationPolicy().filter_viewable_payslips(actor_with(), [FakePayslip(1)])

    def test_filter_for_anonymous_raises(self):
        with pytest.raises(AuthorizationError):
            PayrollAuthorizationPolicy().filter_viewable_payslips(PayrollActor.anonymous(), [FakePayslip(1)])

    def test_payslip_target_is_a_valid_policy_target(self):
        PayrollAuthorizationPolicy().authorize_view_payslip(
            actor_with(PayrollPermissions.PAYSLIP_VIEW), PayslipTarget(payslip_id=1, employee_id=2)
        )

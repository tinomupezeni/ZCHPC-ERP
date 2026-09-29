"""
Object-level authorization for payroll operations.

RBACMiddleware only answers "may this user reach the payroll routes at all".
This policy answers "may this actor perform *this* operation on *this*
target", and is called by the application services *before* any sensitive data
is loaded or any record is changed.

Every ``authorize_*`` method returns None or raises :class:`AuthorizationError`.

Current semantics are deliberately minimal: holding the capability permits the
operation for any target employee. That is the only rule the repository
establishes. All target decisions funnel through :meth:`_permits_target`, which
receives the target employee, so a future rule (own record, department,
whatever the business confirms) is a change in that one method and no call
site changes. No such rule is implemented or implied here.

Passing ``None`` as a target means the target could not be resolved (e.g. the
record does not exist). It is still authorized, so that an unauthorized caller
gets the same answer whether or not the record exists.
"""

from dataclasses import dataclass
from typing import Iterable, Protocol

from modules.payroll.application.authorization.actor import PayrollActor
from modules.payroll.application.authorization.permissions import PayrollPermissions
from shared.domain.exceptions import AuthorizationError


class _HasEmployeeId(Protocol):
    employee_id: int


@dataclass(frozen=True)
class PayslipTarget:
    """The minimum identity of a payslip needed to authorize an operation on it."""

    payslip_id: int
    employee_id: int


class PayrollAuthorizationPolicy:
    # ------------------------------------------------------------------
    # Authentication gate
    # ------------------------------------------------------------------

    def require_authenticated(self, actor: PayrollActor | None) -> None:
        if actor is None or not actor.is_authenticated:
            raise AuthorizationError(
                "Authentication is required to access payroll",
                code="UNAUTHENTICATED",
            )

    # ------------------------------------------------------------------
    # Payslips
    # ------------------------------------------------------------------

    def authorize_view_payslip(
        self, actor: PayrollActor | None, payslip: _HasEmployeeId | None
    ) -> None:
        self._authorize(
            actor, PayrollPermissions.PAYSLIP_VIEW, self._employee_of(payslip)
        )

    def authorize_list_payslips(self, actor: PayrollActor | None) -> None:
        """May the actor ask for payslip lists at all; records are filtered separately."""
        self.require_authenticated(actor)
        self._require_capability(actor, PayrollPermissions.PAYSLIP_VIEW)

    def filter_viewable_payslips(
        self, actor: PayrollActor | None, payslips: Iterable[_HasEmployeeId]
    ) -> list:
        """The subset of payslips the actor may view; never the unfiltered input."""
        self.authorize_list_payslips(actor)
        return [
            p
            for p in payslips
            if self._permits_target(
                actor, PayrollPermissions.PAYSLIP_VIEW, p.employee_id
            )
        ]

    def authorize_process_payroll(self, actor: PayrollActor | None) -> None:
        """Running/closing/reopening a payroll period or marking payslips paid."""
        self.require_authenticated(actor)
        self._require_capability(actor, PayrollPermissions.PAYSLIP_PROCESS)

    def authorize_approve_payslip(
        self, actor: PayrollActor | None, payslip: _HasEmployeeId | None
    ) -> None:
        """Approval has its own capability; nothing else implies it."""
        self._authorize(
            actor, PayrollPermissions.PAYSLIP_APPROVE, self._employee_of(payslip)
        )

    # ------------------------------------------------------------------
    # Per-employee payroll data
    # ------------------------------------------------------------------

    def authorize_view_payroll_profile(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.PROFILE_VIEW, target_employee_id)

    def authorize_manage_payroll_profile(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.PROFILE_MANAGE, target_employee_id)

    def authorize_view_statutory_profile(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.STATUTORY_VIEW, target_employee_id)

    def authorize_manage_statutory_profile(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.STATUTORY_MANAGE, target_employee_id)

    def authorize_view_bank_accounts(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.BANK_VIEW, target_employee_id)

    def authorize_manage_bank_accounts(self, actor, target_employee_id) -> None:
        self._authorize(actor, PayrollPermissions.BANK_MANAGE, target_employee_id)

    # ------------------------------------------------------------------
    # Organization-wide payroll information and configuration
    # ------------------------------------------------------------------

    def authorize_view_summary(self, actor: PayrollActor | None) -> None:
        self.require_authenticated(actor)
        self._require_capability(actor, PayrollPermissions.SUMMARY_VIEW)

    def authorize_view_configuration(self, actor: PayrollActor | None) -> None:
        """Tax brackets, exchange rates, allowance and deduction types."""
        self.require_authenticated(actor)
        self._require_capability(actor, PayrollPermissions.CONFIG_VIEW)

    def authorize_manage_configuration(self, actor: PayrollActor | None) -> None:
        self.require_authenticated(actor)
        self._require_capability(actor, PayrollPermissions.CONFIG_MANAGE)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _employee_of(target) -> int | None:
        return None if target is None else target.employee_id

    def _authorize(
        self,
        actor: PayrollActor | None,
        capability: str,
        target_employee_id: int | None,
    ) -> None:
        self.require_authenticated(actor)
        self._require_capability(actor, capability)
        if not self._permits_target(actor, capability, target_employee_id):
            raise AuthorizationError(
                "The actor is not permitted to perform this payroll operation "
                "on this employee",
                code="PAYROLL_TARGET_DENIED",
                details={"required_permission": capability},
            )

    def _require_capability(self, actor: PayrollActor, capability: str) -> None:
        if not actor.has_permission(capability):
            raise AuthorizationError(
                f"Missing required permission '{capability}'",
                code="PAYROLL_PERMISSION_DENIED",
                details={"required_permission": capability},
            )

    def _permits_target(
        self,
        actor: PayrollActor,  # noqa: ARG002 - reserved for target rules
        capability: str,  # noqa: ARG002
        target_employee_id: int | None,  # noqa: ARG002
    ) -> bool:
        """
        Whether a capability the actor already holds extends to this target.

        The only rule the repository establishes today is that it does. Any
        narrowing the business later confirms belongs here and nowhere else.
        """
        return True

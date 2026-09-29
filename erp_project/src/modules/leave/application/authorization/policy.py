"""
Object-level authorization for leave operations.

RBACMiddleware only answers "may this user reach the leave routes at all".
This policy answers "may this actor perform *this* operation on *this*
employee's leave data", and the leave application services call it before
anything is disclosed or changed.

Every ``authorize_*`` method returns None or raises :class:`AuthorizationError`.

Rules (confirmed REM-03 business decision: authority is capability-based):

- An employee may always act on their *own* requests and balances for the
  self-service operations (view, cancel, summary).
- Acting on another employee's data needs the matching capability. Review
  authority comes from ``leave.request.review`` alone - no department,
  department-head or reporting-line relationship is consulted.
- Self-review stays prohibited, by the domain approval policy
  (``DefaultLeaveApprovalPolicy``), not here.

A target of ``None`` means it could not be resolved (the record does not
exist). It is still authorized, against the capability, so an actor without
it gets the same 403 whether or not the record exists.

All capability-based target decisions pass through :meth:`_permits_target`,
which receives the target employee. It returns True because the confirmed
rule is "holding the capability suffices"; it exists so that the decision
has one place to live, not to anticipate a different rule.
"""

from typing import Iterable, Protocol

from modules.leave.application.authorization.actor import LeaveActor
from modules.leave.application.authorization.permissions import LeavePermissions
from shared.domain.exceptions import AuthorizationError


class _HasEmployeeId(Protocol):
    employee_id: int


class LeaveAuthorizationPolicy:
    # ------------------------------------------------------------------
    # Authentication gate
    # ------------------------------------------------------------------

    def require_authenticated(self, actor: LeaveActor | None) -> None:
        if actor is None or not actor.is_authenticated:
            raise AuthorizationError(
                "Authentication is required to access leave",
                code="UNAUTHENTICATED",
            )

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def authorize_submit(self, actor: LeaveActor | None, employee_id: int) -> None:
        """A leave request may only be raised in the actor's own name."""
        self.require_authenticated(actor)
        if not actor.owns(employee_id):
            raise AuthorizationError(
                "A leave request may only be submitted for yourself",
                code="LEAVE_SUBMIT_NOT_OWN",
            )

    def authorize_view_request(self, actor, owner_employee_id: int | None) -> None:
        self._own_or_capability(actor, LeavePermissions.REQUEST_VIEW_ANY, owner_employee_id)

    def authorize_view_employee_requests(self, actor, employee_id: int) -> None:
        """Listing or summarising one employee's requests."""
        self._own_or_capability(actor, LeavePermissions.REQUEST_VIEW_ANY, employee_id)

    def authorize_cancel_request(self, actor, owner_employee_id: int | None) -> None:
        self._own_or_capability(actor, LeavePermissions.REQUEST_CANCEL_ANY, owner_employee_id)

    def authorize_review_request(self, actor, owner_employee_id: int | None) -> None:
        """
        Approve/reject needs the review capability; owning the request never
        substitutes for it. (Reviewing one's own request is then refused by
        the domain approval policy.)
        """
        self.require_authenticated(actor)
        self._require_capability(actor, LeavePermissions.REQUEST_REVIEW)
        self._require_target(actor, LeavePermissions.REQUEST_REVIEW, owner_employee_id)

    def may_view_any_requests(self, actor: LeaveActor | None) -> bool:
        """Whether a request listing may extend beyond the actor's own records."""
        self.require_authenticated(actor)
        return actor.has_permission(LeavePermissions.REQUEST_VIEW_ANY)

    def may_review_requests(self, actor: LeaveActor | None) -> bool:
        self.require_authenticated(actor)
        return actor.has_permission(LeavePermissions.REQUEST_REVIEW)

    def filter_viewable_requests(self, actor, requests: Iterable[_HasEmployeeId]) -> list:
        """The subset the actor may view; never the unfiltered input."""
        self.require_authenticated(actor)
        return [r for r in requests if self._may_own_or_capability(
            actor, LeavePermissions.REQUEST_VIEW_ANY, r.employee_id
        )]

    def filter_reviewable_requests(self, actor, requests: Iterable[_HasEmployeeId]) -> list:
        """
        The subset the actor may review: capability required, and never the
        actor's own requests, which the domain would refuse to let them review.
        """
        self.require_authenticated(actor)
        if not actor.has_permission(LeavePermissions.REQUEST_REVIEW):
            return []
        return [
            r for r in requests
            if not actor.owns(r.employee_id)
            and self._permits_target(actor, LeavePermissions.REQUEST_REVIEW, r.employee_id)
        ]

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------

    def authorize_view_balance(self, actor, owner_employee_id: int | None) -> None:
        self._own_or_capability(actor, LeavePermissions.BALANCE_VIEW_ANY, owner_employee_id)

    def authorize_manage_balance(self, actor, target_employee_id: int | None) -> None:
        """
        Setting entitlement, adjusting and initializing balances. Management
        capability is required even for the actor's own balance.
        """
        self.require_authenticated(actor)
        self._require_capability(actor, LeavePermissions.BALANCE_MANAGE)
        self._require_target(actor, LeavePermissions.BALANCE_MANAGE, target_employee_id)

    # ------------------------------------------------------------------
    # Leave types
    # ------------------------------------------------------------------

    def authorize_manage_types(self, actor: LeaveActor | None) -> None:
        self.require_authenticated(actor)
        self._require_capability(actor, LeavePermissions.TYPE_MANAGE)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _own_or_capability(self, actor, capability: str, owner_employee_id: int | None) -> None:
        self.require_authenticated(actor)
        if actor.owns(owner_employee_id):
            return
        self._require_capability(actor, capability)
        self._require_target(actor, capability, owner_employee_id)

    def _may_own_or_capability(self, actor, capability: str, owner_employee_id) -> bool:
        try:
            self._own_or_capability(actor, capability, owner_employee_id)
        except AuthorizationError:
            return False
        return True

    def _require_capability(self, actor: LeaveActor, capability: str) -> None:
        if not actor.has_permission(capability):
            raise AuthorizationError(
                f"Missing required permission '{capability}'",
                code="LEAVE_PERMISSION_DENIED",
                details={"required_permission": capability},
            )

    def _require_target(self, actor, capability: str, target_employee_id) -> None:
        if not self._permits_target(actor, capability, target_employee_id):
            raise AuthorizationError(
                "The actor is not permitted to perform this leave operation "
                "for this employee",
                code="LEAVE_TARGET_DENIED",
                details={"required_permission": capability},
            )

    def _permits_target(
        self,
        actor: LeaveActor,  # noqa: ARG002
        capability: str,  # noqa: ARG002
        target_employee_id: int | None,  # noqa: ARG002
    ) -> bool:
        """Confirmed rule: holding the capability applies to every employee."""
        return True

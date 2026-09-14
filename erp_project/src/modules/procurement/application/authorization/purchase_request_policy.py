"""
Business-context authorization for the Purchase Request workflow.

This layer sits between RBAC and the application use cases. RBAC answers
"does this actor's role hold the capability?"; this policy additionally answers
"is this actor the right person for *this* request?".

It never decides whether a state transition is legal - that stays with the
PurchaseRequest aggregate, which is invoked after authorization passes.
"""

from modules.procurement.application.authorization.actor import Actor
from modules.procurement.application.authorization.permissions import (
    PurchaseRequestListScope,
    PurchaseRequestPermissions,
)
from modules.procurement.application.interfaces import IOrganizationalDirectory
from modules.procurement.domain.entities import PurchaseRequest
from modules.procurement.domain.value_objects import RequestStatus
from shared.domain.exceptions import AuthorizationError


class PurchaseRequestAuthorizationPolicy:
    """
    Authorization policy for Purchase Request operations.

    Every public ``authorize_*`` method either returns None or raises
    :class:`AuthorizationError`. Nothing is mutated and no domain method is
    invoked from here.

    Args:
        directory: Organizational directory used for context checks. Optional
            only so that operations with no organizational context (view,
            submit, the organization-wide offices) can be authorized without
            one; department head approval fails closed when it is absent.
    """

    def __init__(self, directory: IOrganizationalDirectory | None = None) -> None:
        self._directory = directory

    # ------------------------------------------------------------------
    # Authentication gate
    # ------------------------------------------------------------------

    def require_authenticated(self, actor: Actor | None) -> None:
        """
        Reject anonymous callers before anything else happens.

        Called by use cases before the aggregate is loaded so that an
        unauthenticated caller cannot learn whether a request exists.
        """
        if actor is None or not actor.is_authenticated:
            raise AuthorizationError(
                "Authentication is required to act on purchase requests",
                code="UNAUTHENTICATED",
            )

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def authorize_create(self, actor: Actor | None, requester_id: int) -> None:
        """A request may only be raised in the actor's own name."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.CREATE)
        if actor.is_admin:
            return
        if actor.employee_id is None or actor.employee_id != requester_id:
            raise AuthorizationError(
                "A purchase request may only be raised on the actor's own behalf",
                code="REQUESTER_MISMATCH",
                details={
                    "actor_employee_id": actor.employee_id,
                    "requester_id": requester_id,
                },
            )

    def authorize_list_categories(self, actor: Actor | None) -> None:
        """
        Listing Purchase Request categories (Slice F11-A) requires the same
        capability as raising a request. Deliberately not a new permission:
        seeing the category list is only useful to someone who could use one
        to create a request, and every role granted CREATE already needs to
        see it - introducing a separate category-view permission would just
        be a second knob that has to be kept in sync with the first.
        """
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.CREATE)

    def authorize_view(
        self,
        actor: Actor | None,
        request: PurchaseRequest | None = None,  # noqa: ARG002 - see docstring
    ) -> None:
        """
        Viewing requires the view capability.

        Per-record read scoping is not narrowed here: the existing requirements
        do not define who may read which request, and inventing a rule would
        silently change behaviour. ``request`` is accepted so that callers pass
        the record they are about to disclose and scoping can be added here
        without changing any call site. See the Slice 4 gap notes.
        """
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.VIEW)

    def authorize_list(
        self, actor: Actor | None, scope: PurchaseRequestListScope
    ) -> None:
        """
        Listing is scoped, never unrestricted.

        ``MINE`` needs the view capability; each workflow queue needs that
        stage's own capability, so holding ``view`` alone never discloses other
        people's requests. Which records a scope actually yields is the listing
        use case's job - this only decides whether the actor may ask.
        """
        self.require_authenticated(actor)
        self._require_permission(actor, scope.required_permission)

        if scope is not PurchaseRequestListScope.MINE:
            return

        if not actor.is_admin and actor.employee_id is None:
            raise AuthorizationError(
                "Listing your own purchase requests requires an employee profile",
                code="NO_EMPLOYEE_PROFILE",
            )

    def authorize_submit(self, actor: Actor | None, request: PurchaseRequest) -> None:
        """Only the requester submits their own request."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.SUBMIT)
        self._require_requester(actor, request, action="submit")

    def authorize_department_head_approval(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """Department head approval is scoped to the request's department."""
        self.require_authenticated(actor)
        self._require_permission(
            actor, PurchaseRequestPermissions.DEPARTMENT_HEAD_APPROVE
        )
        self._require_employee_identity(actor)
        self._require_department_authority(actor, request)
        self._require_not_requester(actor, request)

    def authorize_accounts_verification(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """Accounts verification is an organization-wide office, not department-scoped."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.ACCOUNTS_VERIFY)
        self._require_employee_identity(actor)
        self._require_not_requester(actor, request)

    def authorize_gm_recommendation(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """GM recommendation is an organization-wide office."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.GM_RECOMMEND)
        self._require_employee_identity(actor)
        self._require_not_requester(actor, request)

    def authorize_director_approval(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """Director approval is an organization-wide office."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.DIRECTOR_APPROVE)
        self._require_employee_identity(actor)
        self._require_not_requester(actor, request)

    def authorize_processing(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """Procurement processing is an organization-wide office."""
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.PROCESS)
        self._require_employee_identity(actor)
        self._require_not_requester(actor, request)

    def authorize_rejection(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """
        Rejection requires the reject capability *and* authority over the stage
        the request is currently sitting at, so that holding ``reject`` alone
        cannot kill a request waiting at another office's desk.
        """
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.REJECT)
        self._require_employee_identity(actor)
        self._require_stage_authority(actor, request)
        self._require_not_requester(actor, request)

    def authorize_correction_and_resubmission(
        self, actor: Actor | None, request: PurchaseRequest
    ) -> None:
        """
        Correcting a rejected request and putting it back into the workflow is
        the requester's own action, and requires both capabilities because the
        domain performs both steps in one transition.
        """
        self.require_authenticated(actor)
        self._require_permission(actor, PurchaseRequestPermissions.CORRECT)
        self._require_permission(actor, PurchaseRequestPermissions.RESUBMIT)
        self._require_requester(actor, request, action="correct and resubmit")

    # ------------------------------------------------------------------
    # Internal checks
    # ------------------------------------------------------------------

    def _require_employee_identity(self, actor: Actor) -> None:
        """
        Workflow decisions are attributed to an employee.

        ``PurchaseRequestDecision.actor`` is a non-nullable employee reference,
        so an authenticated user with no employee profile - a bare superuser,
        for instance - cannot sign a stage of this workflow. Admins are not
        exempt: an unattributable approval is refused here rather than failing
        as an integrity error on save.
        """
        if actor.employee_id is None:
            raise AuthorizationError(
                "Acting on a purchase request requires an employee profile",
                code="NO_EMPLOYEE_PROFILE",
            )

    def _require_permission(self, actor: Actor, permission: str) -> None:
        """RBAC gate: the actor's role must grant the capability."""
        if not actor.has_permission(permission):
            raise AuthorizationError(
                f"Missing required permission '{permission}'",
                code="PERMISSION_DENIED",
                details={"required_permission": permission},
            )

    def _require_requester(
        self, actor: Actor, request: PurchaseRequest, action: str
    ) -> None:
        """The actor must own the request."""
        if actor.is_admin:
            return
        if actor.employee_id is None or actor.employee_id != request.requester_id:
            raise AuthorizationError(
                f"Only the requester may {action} this purchase request",
                code="NOT_REQUESTER",
                details={"purchase_request_id": request.id},
            )

    def _require_not_requester(self, actor: Actor, request: PurchaseRequest) -> None:
        """
        Self-approval prohibition.

        Established by the existing workflow rules - the legacy requisition
        approval views and ApprovalWorkflow both refuse a requester acting on
        their own request - and it applies to admins too.
        """
        if actor.employee_id is not None and actor.employee_id == request.requester_id:
            raise AuthorizationError(
                "The requester may not act on their own purchase request",
                code="SELF_APPROVAL_FORBIDDEN",
                details={"purchase_request_id": request.id},
            )

    def _require_department_authority(
        self, actor: Actor, request: PurchaseRequest
    ) -> None:
        """
        Establish that the actor is the authority over this request's department.

        Authority comes from one authoritative relationship and nothing else:

            PurchaseRequest.department -> Department.head -> Employees

        Belonging to the department is explicitly not sufficient: a colleague
        who happens to hold the capability is not the department's head.

        Fails closed - if no directory is wired in, or the department has no
        head on record, nobody holds departmental authority over it.
        """
        if actor.is_admin:
            return

        self._require_employee_identity(actor)

        if self._directory is None:
            raise AuthorizationError(
                "Departmental authority cannot be established without an "
                "organizational directory",
                code="DEPARTMENT_CONTEXT_DENIED",
                details={"request_department_id": request.department_id},
            )

        head_id = self._directory.get_department_head_id(request.department_id)

        if head_id is None:
            raise AuthorizationError(
                "No department head is recorded for this purchase request's department",
                code="DEPARTMENT_HEAD_NOT_RECORDED",
                details={"request_department_id": request.department_id},
            )

        if head_id != actor.employee_id:
            raise AuthorizationError(
                "The actor is not the recorded head of this purchase request's department",
                code="DEPARTMENT_CONTEXT_DENIED",
                details={"request_department_id": request.department_id},
            )

    def _require_stage_authority(self, actor: Actor, request: PurchaseRequest) -> None:
        """
        The actor must hold the capability (and context) of the stage the
        request is currently awaiting.
        """
        status = request.status

        if status == RequestStatus.PENDING_DEPARTMENT_HEAD:
            self._require_permission(
                actor, PurchaseRequestPermissions.DEPARTMENT_HEAD_APPROVE
            )
            self._require_department_authority(actor, request)
            return
        if status == RequestStatus.PENDING_ACCOUNTS:
            self._require_permission(actor, PurchaseRequestPermissions.ACCOUNTS_VERIFY)
            return
        if status == RequestStatus.PENDING_GM:
            self._require_permission(actor, PurchaseRequestPermissions.GM_RECOMMEND)
            return
        if status == RequestStatus.PENDING_DIRECTOR:
            self._require_permission(actor, PurchaseRequestPermissions.DIRECTOR_APPROVE)
            return
        if status == RequestStatus.PENDING_PROCUREMENT:
            self._require_permission(actor, PurchaseRequestPermissions.PROCESS)
            return

        # DRAFT / PROCESSED / REJECTED have no pending approver. Authorization
        # does not decide that - the domain rejects the transition - so the
        # actor is let through to the aggregate, which raises ValidationError.

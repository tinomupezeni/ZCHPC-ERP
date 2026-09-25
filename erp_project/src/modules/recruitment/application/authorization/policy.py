"""
Authorization for internal recruitment operations.

RBACMiddleware only answers "may this user reach the recruitment routes at
all" - and any ``recruitment.*`` permission is enough for that. This policy
answers "may this actor perform *this* operation", and the recruitment
application services call it before anything is disclosed or changed.

Every ``authorize_*`` method returns None or raises :class:`AuthorizationError`.

Rules (REM-04): authority is capability-based. Jobs, candidates and
applications are organisation-level records; no department, reporting-line or
ownership relationship is consulted, because no business rule asks for one.

Authorization runs before the target is looked up, so an actor without the
capability gets the same 403 whether or not the record exists.
"""

from modules.recruitment.application.authorization.actor import RecruitmentActor
from modules.recruitment.application.authorization.permissions import RecruitmentPermissions
from shared.domain.exceptions import AuthorizationError


class RecruitmentAuthorizationPolicy:
    def require_authenticated(self, actor: RecruitmentActor | None) -> None:
        if actor is None or not actor.is_authenticated:
            raise AuthorizationError(
                "Authentication is required to access recruitment",
                code="UNAUTHENTICATED",
            )

    def authorize_view_jobs(self, actor: RecruitmentActor | None) -> None:
        """Internal job listing/detail, including Draft, Pending and Closed jobs."""
        self._require(actor, RecruitmentPermissions.JOB_VIEW)

    def authorize_manage_jobs(self, actor: RecruitmentActor | None) -> None:
        """Create, update, delete, publish, close and reopen jobs."""
        self._require(actor, RecruitmentPermissions.JOB_MANAGE)

    def authorize_view_applications(self, actor: RecruitmentActor | None) -> None:
        """Applications and the candidate data they carry."""
        self._require(actor, RecruitmentPermissions.APPLICATION_VIEW)

    def authorize_review_applications(self, actor: RecruitmentActor | None) -> None:
        """Application status transitions."""
        self._require(actor, RecruitmentPermissions.APPLICATION_REVIEW)

    def _require(self, actor: RecruitmentActor | None, capability: str) -> None:
        self.require_authenticated(actor)
        if not actor.has_permission(capability):
            raise AuthorizationError(
                f"Missing required permission '{capability}'",
                code="RECRUITMENT_PERMISSION_DENIED",
                details={"required_permission": capability},
            )

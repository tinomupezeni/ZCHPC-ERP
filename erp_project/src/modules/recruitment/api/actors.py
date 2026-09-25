"""
Resolve the authenticated request into a RecruitmentActor.

The single place acting identity enters the recruitment application layer.
Permissions come from the shared ``resolve_actor_permissions`` (including its
superuser handling), not re-derived here.
"""

from modules.hr.application.authorization import resolve_actor_permissions
from modules.recruitment.application.authorization import RecruitmentActor


def recruitment_actor_from_request(request) -> RecruitmentActor:
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return RecruitmentActor.anonymous()

    return RecruitmentActor(
        permissions=resolve_actor_permissions(user),
        is_superuser=bool(getattr(user, "is_superuser", False)),
        is_authenticated=True,
    )

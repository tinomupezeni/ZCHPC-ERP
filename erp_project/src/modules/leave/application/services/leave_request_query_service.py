"""
The organization-wide leave request listing (``/leave/requests/all/``).

This is a read model: the HR admin page needs employee and reviewer names, so
it reads the Django model with its relations rather than the domain
repository, as the view did before. What this adds is the authorization
boundary that listing never had beyond a role-name check:

- an actor holding ``leave.request.view_any`` gets every request;
- anyone else gets only their own requests;
- either way each record passes through the policy's per-record filter.
"""

from modules.leave.application.authorization import (
    LeaveActor,
    LeaveAuthorizationPolicy,
)
from modules.leave.infrastructure.persistence.models import LeaveRequest as LeaveRequestModel


class LeaveRequestQueryService:
    def __init__(self, policy: LeaveAuthorizationPolicy | None = None) -> None:
        self._policy = policy or LeaveAuthorizationPolicy()

    def list_requests(self, actor: LeaveActor) -> list:
        queryset = LeaveRequestModel.objects.select_related(
            "employee", "leave_type", "reviewed_by"
        )
        if not self._policy.may_view_any_requests(actor):
            if actor.employee_id is None:
                return []
            queryset = queryset.filter(employee_id=actor.employee_id)
        return self._policy.filter_viewable_requests(actor, queryset)

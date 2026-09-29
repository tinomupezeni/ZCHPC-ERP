"""
Read-only workflow actions for a purchase request.

Lists the labeled actions the current actor may attempt from the
record's present state, resolved from the seeded workflow chain by
capability (and document attributes for conditions). Advisory by
contract: the aggregate guards and the authorization policy still
enforce state legality and business context on execution, so a listed
action can still be refused with 403 when context checks fail.
"""

from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from modules.procurement.api.actors import actor_from_request
from modules.procurement.api.purchase_request_views import (
    _handle_domain_error,
    _policy,
    _repository,
)
from modules.procurement.application.use_cases import ViewPurchaseRequest
from modules.workflow.application.services import WorkflowEngine
from modules.workflow.infrastructure.persistence.django_workflow_repository import (
    DjangoWorkflowRepository,
)
from shared.domain.exceptions import DomainException

DOCUMENT_TYPE = "procurement.PurchaseRequest"

_engine = WorkflowEngine(DjangoWorkflowRepository())


@api_view(["GET"])
def purchase_request_actions(request: Request, request_id: int) -> Response:
    """List attemptable workflow actions for one purchase request."""
    actor = actor_from_request(request)
    try:
        record = ViewPurchaseRequest(_repository, _policy).execute(request_id, actor)
    except DomainException as exc:
        return _handle_domain_error(exc)

    transitions = _engine.available_actions(
        DOCUMENT_TYPE,
        record.status.value,
        actor,
        attrs={"total_estimated_cost": float(record.total_estimated_cost)},
        is_owner=(actor.employee_id is not None and actor.employee_id == record.requester_id),
    )
    return Response(
        [
            {
                "action": t.action,
                "label": t.label,
                "next_state": t.next_state,
            }
            for t in transitions
        ]
    )

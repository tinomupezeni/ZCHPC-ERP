"""Application services for the workflow module."""

from modules.workflow.application.interfaces.repositories import (
    IWorkflowRepository,
)
from modules.workflow.domain.entities.workflow import (
    ActorPermissions,
    WorkflowTransition,
)


class WorkflowEngine:
    """Resolves workflow actions from stored chains.

    Given a document type, its current state, the actor's capabilities,
    and document attributes, returns the transitions the actor may
    attempt. Advisory by contract: aggregates enforce state guards and
    module policies enforce business context on execution.
    """

    def __init__(self, repository: IWorkflowRepository) -> None:
        self._repository = repository

    def available_actions(
        self,
        document_type: str,
        current_state: str,
        actor: ActorPermissions,
        attrs: dict | None = None,
        is_owner: bool = False,
    ) -> list[WorkflowTransition]:
        """Transitions attemptable now; empty when no chain is seeded."""
        workflow = self._repository.get_active(document_type)
        if workflow is None or not workflow.is_active:
            return []
        return workflow.available_actions(current_state, actor, attrs or {}, is_owner)

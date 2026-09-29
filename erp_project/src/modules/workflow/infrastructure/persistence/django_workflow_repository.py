"""Django repository implementing the workflow persistence contract."""

from modules.workflow.application.interfaces.repositories import (
    IWorkflowRepository,
)
from modules.workflow.domain.entities import (
    Workflow as DomainWorkflow,
)
from modules.workflow.domain.entities import (
    WorkflowCondition as DomainCondition,
)
from modules.workflow.domain.entities import (
    WorkflowState as DomainState,
)
from modules.workflow.domain.entities import (
    WorkflowTransition as DomainTransition,
)
from modules.workflow.infrastructure.persistence import models as orm


class DjangoWorkflowRepository(IWorkflowRepository):
    """Loads stored chains into domain objects."""

    def get_active(self, document_type: str) -> DomainWorkflow | None:
        """Return the active chain for a document type, if seeded."""
        try:
            record = orm.Workflow.objects.prefetch_related("states", "transitions__conditions").get(
                document_type=document_type, is_active=True
            )
        except orm.Workflow.DoesNotExist:
            return None
        return DomainWorkflow(
            name=record.name,
            document_type=record.document_type,
            is_active=record.is_active,
            states=[DomainState(state=s.state) for s in record.states.all()],
            transitions=[
                DomainTransition(
                    action=t.action,
                    label=t.label,
                    state=t.state,
                    next_state=t.next_state,
                    required_permissions=tuple(t.required_permissions or []),
                    allow_self_approval=t.allow_self_approval,
                    conditions=tuple(
                        DomainCondition(
                            field=c.field,
                            operator=c.operator,
                            value=c.value,
                        )
                        for c in t.conditions.all()
                    ),
                )
                for t in record.transitions.all()
            ],
        )

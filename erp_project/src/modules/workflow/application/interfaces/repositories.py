"""Repository contracts for the workflow module."""

from abc import ABC, abstractmethod

from modules.workflow.domain.entities import Workflow


class IWorkflowRepository(ABC):
    """Persistence contract for approval chains."""

    @abstractmethod
    def get_active(self, document_type: str) -> Workflow | None:
        """Return the active workflow for a document type, if one exists."""
        ...

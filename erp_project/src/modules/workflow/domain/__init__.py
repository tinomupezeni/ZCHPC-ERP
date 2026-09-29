"""
Workflow module domain layer.

Generic declarative approval chains: states, transitions, and structured
conditions as data. See entities/workflow.py for the enforcement contract.
"""

from modules.workflow.domain.entities import (
    Workflow,
    WorkflowCondition,
    WorkflowState,
    WorkflowTransition,
)

__all__ = [
    "Workflow",
    "WorkflowCondition",
    "WorkflowState",
    "WorkflowTransition",
]

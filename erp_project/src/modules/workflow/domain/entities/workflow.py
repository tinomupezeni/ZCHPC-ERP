"""
Generic declarative workflow engine (domain layer).

Models an approval chain as data instead of if-branches:

- ``Workflow``: one active chain per document type (e.g. purchase requests).
- ``WorkflowState``: a named step in the chain.
- ``WorkflowTransition``: a labeled action moving one state to the next,
  gated by required capabilities, an optional self-approval rule, and
  structured conditions (field/operator/value rows - never expressions).
- ``WorkflowCondition``: one predicate on document attributes.

Enforcement stays hybrid by design: this engine *resolves* which actions
an actor may attempt; the document aggregate keeps its own guards as the
final invariant, and the module's authorization policy keeps any
business-context checks (department authority, requester exclusion).
Listing is therefore capability-level and advisory - execution enforces.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


class ActorPermissions(Protocol):
    """Minimal surface the engine needs from any module's actor."""

    def has_permission(self, permission: str) -> bool: ...


@dataclass(frozen=True)
class WorkflowCondition:
    """One structured predicate on document attributes.

    Attributes:
        field: Attribute name looked up in the document attrs mapping.
        operator: One of eq, ne, gt, gte, lt, lte, in, not_in.
        value: Compared against; lists only for in/not_in.
    """

    field: str
    operator: str
    value: Any

    VALID_OPERATORS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in"})

    def satisfied_by(self, attrs: dict[str, Any]) -> bool:
        """Evaluate against document attributes; missing field fails closed."""
        if self.operator not in self.VALID_OPERATORS:
            return False
        if self.field not in attrs:
            return False
        actual = attrs[self.field]
        try:
            if self.operator == "eq":
                return actual == self.value
            if self.operator == "ne":
                return actual != self.value
            if self.operator == "gt":
                return actual > self.value
            if self.operator == "gte":
                return actual >= self.value
            if self.operator == "lt":
                return actual < self.value
            if self.operator == "lte":
                return actual <= self.value
            if self.operator == "in":
                return actual in self.value
            return actual not in self.value  # not_in
        except TypeError:
            return False


@dataclass(frozen=True)
class WorkflowTransition:
    """One labeled action between two states.

    Attributes:
        action: Machine name (e.g. "approve").
        label: UI copy (e.g. "Approve").
        state: Required current state value.
        next_state: State value after the action.
        required_permissions: Every capability the actor must hold.
        allow_self_approval: Whether the actor may act on their own
            document. Defaults False (finance chains forbid it).
        conditions: All must be satisfied by document attributes.
    """

    action: str
    label: str
    state: str
    next_state: str
    required_permissions: tuple[str, ...] = ()
    allow_self_approval: bool = False
    conditions: tuple["WorkflowCondition", ...] = ()

    def available_to(
        self,
        actor: ActorPermissions,
        attrs: dict[str, Any],
        is_owner: bool,
    ) -> bool:
        """Capability-level check: permissions, self-approval, conditions."""
        if not self.allow_self_approval and is_owner:
            return False
        if not all(actor.has_permission(p) for p in self.required_permissions):
            return False
        return all(c.satisfied_by(attrs) for c in self.conditions)


@dataclass(frozen=True)
class WorkflowState:
    """One named step in a workflow."""

    state: str


@dataclass
class Workflow:
    """One active approval chain for a document type."""

    name: str
    document_type: str
    is_active: bool = True
    states: list[WorkflowState] = field(default_factory=list)
    transitions: list[WorkflowTransition] = field(default_factory=list)

    def available_actions(
        self,
        current_state: str,
        actor: ActorPermissions,
        attrs: dict[str, Any] | None = None,
        is_owner: bool = False,
    ) -> list[WorkflowTransition]:
        """Transitions the actor may attempt from the current state.

        Advisory: the aggregate and the module policy still enforce on
        execution (state guards, department authority, requester rules).
        """
        attrs = attrs or {}
        return [t for t in self.transitions if t.state == current_state and t.available_to(actor, attrs, is_owner)]

"""
Tests for the generic workflow engine (pure domain, no database).

Covers state filtering, capability gating, self-approval, structured
conditions (including fail-closed on missing fields and type errors),
and the engine's empty result when no chain is seeded.
"""

from modules.workflow.application.services import WorkflowEngine
from modules.workflow.domain.entities import (
    Workflow,
    WorkflowCondition,
    WorkflowState,
    WorkflowTransition,
)


class StubActor:
    """Minimal actor carrying a capability set."""

    def __init__(self, permissions=(), authenticated=True):
        self._permissions = set(permissions)
        self._authenticated = authenticated

    def has_permission(self, permission):
        return self._authenticated and permission in self._permissions


class StubRepository:
    """In-memory chain store behind the repository contract."""

    def __init__(self, workflow=None):
        self._workflow = workflow

    def get_active(self, document_type):  # noqa: ARG002 - stub ignores type
        return self._workflow


def make_chain():
    return Workflow(
        name="Test Chain",
        document_type="test.Document",
        states=[WorkflowState("DRAFT"), WorkflowState("PENDING"), WorkflowState("DONE")],
        transitions=[
            WorkflowTransition(
                action="submit",
                label="Submit",
                state="DRAFT",
                next_state="PENDING",
                required_permissions=("test.submit",),
            ),
            WorkflowTransition(
                action="approve",
                label="Approve",
                state="PENDING",
                next_state="DONE",
                required_permissions=("test.approve",),
                conditions=(WorkflowCondition(field="total", operator="gte", value=100),),
            ),
            WorkflowTransition(
                action="self-close",
                label="Close",
                state="PENDING",
                next_state="DONE",
                required_permissions=("test.approve",),
                allow_self_approval=True,
            ),
        ],
    )


def test_lists_submit_for_capable_actor():
    engine = WorkflowEngine(StubRepository(make_chain()))
    actions = engine.available_actions("test.Document", "DRAFT", StubActor(("test.submit",)))
    assert [t.action for t in actions] == ["submit"]


def test_hides_actions_without_capability():
    engine = WorkflowEngine(StubRepository(make_chain()))
    assert engine.available_actions("test.Document", "DRAFT", StubActor()) == []


def test_state_filters_transitions():
    engine = WorkflowEngine(StubRepository(make_chain()))
    actor = StubActor(("test.submit", "test.approve"))
    actions = engine.available_actions("test.Document", "DRAFT", actor, attrs={"total": 500})
    assert [t.action for t in actions] == ["submit"]


def test_condition_gates_expensive_approval():
    engine = WorkflowEngine(StubRepository(make_chain()))
    actor = StubActor(("test.approve",))
    affordable = engine.available_actions("test.Document", "PENDING", actor, attrs={"total": 50})
    assert [t.action for t in affordable] == ["self-close"]
    pricey = engine.available_actions("test.Document", "PENDING", actor, attrs={"total": 500})
    assert sorted(t.action for t in pricey) == ["approve", "self-close"]


def test_missing_field_fails_closed():
    engine = WorkflowEngine(StubRepository(make_chain()))
    actor = StubActor(("test.approve",))
    actions = engine.available_actions("test.Document", "PENDING", actor, attrs={})
    assert [t.action for t in actions] == ["self-close"]


def test_self_approval_forbidden_by_default():
    engine = WorkflowEngine(StubRepository(make_chain()))
    actor = StubActor(("test.approve",))
    actions = engine.available_actions(
        "test.Document",
        "PENDING",
        actor,
        attrs={"total": 500},
        is_owner=True,
    )
    assert [t.action for t in actions] == ["self-close"]


def test_no_chain_seeded_returns_empty():
    engine = WorkflowEngine(StubRepository(None))
    assert engine.available_actions("test.Document", "DRAFT", StubActor()) == []


def test_inactive_chain_returns_empty():
    chain = make_chain()
    chain.is_active = False
    engine = WorkflowEngine(StubRepository(chain))
    assert engine.available_actions("test.Document", "DRAFT", StubActor()) == []


def test_unknown_operator_fails_closed():
    transition = WorkflowTransition(
        action="x",
        label="X",
        state="DRAFT",
        next_state="PENDING",
        conditions=(WorkflowCondition(field="total", operator="approx", value=1),),
    )
    assert transition.available_to(StubActor(), {"total": 1}, False) is False

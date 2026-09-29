# Workflow Module

Generic declarative approval chains shared by all business modules.

## Idea

An approval chain is data (states, transitions, conditions), not
if-branches. The engine resolves which labeled actions an actor may
attempt; document aggregates keep their state guards and module
authorization policies keep business-context checks on execution.

## Layout

- `domain/entities/workflow.py` — `Workflow`, `WorkflowState`,
  `WorkflowTransition`, `WorkflowCondition` (pure, no dependencies).
- `application/services/workflow_engine.py` — `WorkflowEngine`.
- `application/interfaces/repositories.py` — `IWorkflowRepository`.
- `infrastructure/persistence/` — Django models + repository.
- `migrations/` — `0001` schema, `0002` seeds the pilot chain.
- `tests/` — engine unit tests (no database).

## Pilot: purchase requests

`0002_seed_purchase_request_workflow` mirrors the live
`DRAFT → … → PROCESSED` chain (8 states, 11 transitions, self-approval
forbidden everywhere, no conditions yet). Served at
`GET /api/v2/procurement/requests/<id>/actions/` →
`[{action, label, next_state}]` (see
`modules.procurement.api.workflow_actions_views`).

## Adding another document

1. Seed a `Workflow` row set for its states/transitions.
2. Expose an actions endpoint in the owning module calling
   `WorkflowEngine.available_actions`.
3. Keep aggregate guards and policy checks untouched.

## Rules

- Conditions are field/operator/value rows. No expressions, no eval.
- Listing is advisory; execution enforces.
- Statuses keep their values — seeding never migrates document data.

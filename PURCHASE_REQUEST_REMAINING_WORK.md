# Purchase Request Module — Handoff Summary

**Branch:** `forms/purchase-requisition`
**Status as of this handoff:** Employee → Department Head → Accounts → General Manager → Director approval chain is complete and demoed. Procurement Processing (the final stage) is not yet built on the frontend; the backend contract for it already exists.

---

## 1. Overview

This document summarizes the current state of the Purchase Request (Purchase Requisition) feature for handoff to a supervisor or another developer. It covers what has been implemented, how it has been validated, what remains, and what has been deliberately deferred pending business input.

It is written against the actual code and git history on this branch, not from a plan or specification — see individual sections for the files and endpoints referenced.

## 2. Current Workflow

```
Employee
  ↓ (submit)
Department Head
  ↓ (approve)
Accounts
  ↓ (verify)
General Manager
  ↓ (recommend)
Director
  ↓ (approve)
Procurement   ← backend contract exists; no frontend UI yet (see §12)
```

Backend status values: `DRAFT → PENDING_DEPARTMENT_HEAD → PENDING_ACCOUNTS → PENDING_GM → PENDING_DIRECTOR → PENDING_PROCUREMENT → PROCESSED`, with a terminal `REJECTED` reachable from any of the four approval stages (not from `PENDING_PROCUREMENT` — see §12).

## 3. Completed Implementation

Backend (`erp_project/src/modules/procurement/`):
- Purchase Request domain aggregate, value objects, and domain events (`domain/entities/purchase_request.py`, `domain/value_objects/procurement_types.py`, `domain/events/procurement_events.py`)
- Application use cases for create, submit, approve at each stage, reject, correct-and-resubmit, and process (`application/use_cases/purchase_request_use_cases.py`)
- `PurchaseRequestAuthorizationPolicy` — one `authorize_*` method per stage, each requiring authentication, the stage's specific permission, a real employee identity, and that the actor is not the requester (`application/authorization/purchase_request_policy.py`)
- Django persistence, migrations, and the Purchase Request API (`infrastructure/persistence/`, `api/`)
- Official ZCHPC Chart of Accounts import and an employee-facing category → AccountChart mapping (`domain/entities/purchase_request_category.py`, `seed_purchase_request_categories.py`)
- Department Head assignment (HR module)
- Timezone-aware aggregate timestamps
- `seed_pr_test_data` management command, seeding one test account per workflow stage (see §15)
- Unit, policy, and integration/e2e test coverage (§10)

Frontend (`employee-portal/src/`):
- Purchase Request submission form, draft/rejected-request editing, and draft deletion
- Request status UX for the requester, including corrected/resubmitted request handling
- Department Head review, Accounts verification, GM recommendation, and Director approval review pages
- Reviewer access detection driven by real backend authorization (not a client-side role guess)
- Corporate Purchase Requisition document layout used consistently across requester and reviewer views
- Purchase Request notifications surfaced in the portal

## 4. Employee Portal Functionality

An employee can create a draft request, add/edit line items with category, quantity, cost, and expected delivery period, save as draft, submit, and — if rejected — correct and resubmit without losing the original request's audit trail. Drafts can be deleted. The employee's own request list and detail view show the current status, the full approval history, and (if rejected) the rejection reason.

## 5. Reviewer Workflows

Four reviewer stages exist as dedicated pages, each following the same pattern (queue page → shared `PurchaseRequestDetail` view → approve/reject action dialog):

| Stage | Frontend page | Backend endpoint | Permission |
|---|---|---|---|
| Department Head | `PurchaseRequestReviewPage.tsx` | `POST .../department-head/approve/` | `procurement.purchase_request.department_head_approve` |
| Accounts | `PurchaseRequestAccountsReviewPage.tsx` | `POST .../accounts/verify/` | `procurement.purchase_request.accounts_verify` |
| General Manager | `PurchaseRequestGMReviewPage.tsx` | `POST .../gm/recommend/` | `procurement.purchase_request.gm_recommend` |
| Director | `PurchaseRequestDirectorReviewPage.tsx` | `POST .../director/approve/` | `procurement.purchase_request.director_approve` |

Rejection at any of the four stages uses one shared, stage-aware endpoint: `POST .../requests/{id}/reject/` with a required `reason`. It rejects at whichever stage the request currently sits at.

## 6. Authorization / RBAC

Two layers:
- **Route-level:** `RBACMiddleware` gates coarse module access.
- **Action-level:** `PurchaseRequestAuthorizationPolicy` — a dedicated `authorize_*` method per stage. Department Head approval is department-scoped (the actor must head the request's own department); Accounts, GM, Director, and Procurement processing are organization-wide capabilities with no department scoping.

The frontend does not infer a reviewer's role from a role name. `usePurchaseRequestReviewerAccess` probes each real queue endpoint and only shows the corresponding sidebar item and route if the backend actually returns success — a 403 hides the item rather than the frontend guessing who should see what.

## 7. Notifications

Three domain events currently produce a requester-facing notification (`modules/portal/event_handlers.py`):
- `PurchaseRequestRejected`
- `PurchaseRequestCorrectedAndResubmitted`
- `PurchaseRequestProcessed`

Department Head approval, Accounts verification, GM recommendation, and Director approval do **not** currently emit a notification — this is the existing backend contract, not a gap introduced by this work. See §13 (F27) for the deferred decision on whether to expand this.

## 8. Corporate Document UX

`PurchaseRequestDetail.tsx` renders a single, reusable corporate Purchase Requisition document (`DocumentSection`/`DocumentField` components) used identically by the requester's own view and by all four reviewer stages, varying only in the status banner copy and which actions are shown. This avoids one bespoke layout per stage.

## 9. Approval History / Auditability

Every approval, verification, recommendation, and rejection is appended to the request's `decisions` array (stage, decision, actor, reason, timestamp) and returned in full by the API. The "Approval Workflow" section of `PurchaseRequestDetail` renders the complete history plus the current pending stage — it does not collapse or summarize prior decisions.

Note: this history array covers the four approval stages only (`DEPARTMENT_HEAD`, `ACCOUNTS`, `GM`, `DIRECTOR`). Procurement processing does not append to it — see §12.

A CSS-only defect in the shared `ScrollArea` component (used to make the document scrollable inside its dialog) was found and fixed during manual QA: for tall requests, the lower part of the Approval Workflow section was visually clipped with no scrollbar, which could look like missing decision history even though the underlying data and rendering logic were always correct. Confirmed via direct inspection that the API response and the DOM both already contained the complete history before this fix; the fix itself touches only `employee-portal/src/components/ui/scroll-area.tsx` and does not change any Purchase Request file.

## 10. Current Testing / Validation

- **Frontend:** 402/402 tests passing across 26 test files (`npx vitest run`); `tsc --noEmit` clean; production build succeeds; ESLint clean on all changed files (only pre-existing, unrelated findings elsewhere in the project).
- **Backend:** the full Purchase Request unit, policy, use-case, integration, and e2e suite passes — 313/313 (`pytest`), including `test_happy_path.py` (full workflow through the real stack), `test_notifications.py`, `test_rejection_flow.py`, `test_transitions_and_queues.py` (invalid-transition and queue-isolation coverage), and `test_authorization.py`, plus all Director-specific policy/use-case tests. A separate, pre-existing legacy suite for unrelated `PurchaseOrder`/`BudgetCenter`/`Vendor` entities has failures that were confirmed to also exist identically on `main` — not introduced by this work.
- **Manual QA:** full Employee → Department Head → Accounts → GM → Director cycle exercised against the real local API and Postgres database, for both the approval path (→ `PENDING_PROCUREMENT`) and the rejection path (→ `REJECTED`, reason preserved and visible to the requester, prior decisions retained). Unauthorized direct navigation to a reviewer route is blocked by the backend (403), not merely hidden in the UI.
- `git diff --check`: clean for the changes on this branch (no new whitespace issues).

## 11. Current Project State

The workflow is feature-complete and demoed through Director approval. A request that clears Director approval sits at `PENDING_PROCUREMENT` with no way for a Procurement Officer to act on it yet from the UI — see §12.

## 12. Remaining Work

### F23 — Procurement Processing (recommended next step)

Investigated against the actual backend rather than assumed:

- The endpoint already exists: `POST /api/v2/procurement/requests/{id}/process/`, permission `procurement.purchase_request.process`, queue scope `pending-procurement` (`GET /procurement/requests/?scope=pending-procurement`).
- Transition: `PENDING_PROCUREMENT → PROCESSED`. It sets `processed_by` and `processed_at` directly on the request.
- It does **not** append an entry to the `decisions` history array — `DecisionStage` has no `PROCUREMENT` value. Processing is recorded only via `processed_by`/`processed_at`, not as a stage decision.
- It accepts no request body today — no supplier, purchase order, or reference number is captured.
- There is currently no reject/decline path once a request reaches `PENDING_PROCUREMENT` — the shared `reject()` domain method only recognizes the four approval stages.
- It already emits `PurchaseRequestProcessed`, which already produces a requester notification (§7).
- A seeded test account for this role already exists (`seed_pr_test_data`, "Pat Procure", `PR_TEST_PROCUREMENT`, granted `PROCESS` + `VIEW`) — no seed changes are needed to start frontend work.

**Nothing on the frontend consumes this endpoint yet** — no service method, no queue page, no reviewer-access wiring, no sidebar entry. F23 is a frontend build against an already-defined backend contract, not a from-scratch design. Before implementing, confirm with the business/Procurement stakeholders whether processing should capture supplier/PO information and whether a decline path is actually needed at this stage — the current backend does not require or support either, so building UI for them would be inventing scope.

### F24 — End-to-End Purchase Request Lifecycle Hardening

Full lifecycle coverage once F23 exists: approval and rejection paths end-to-end, correction/resubmission, authorization failures, unauthorized direct navigation, invalid state transitions, duplicate actions/submissions, refresh/reload behavior, decision-history integrity, notifications, API/network failures, empty/error states, both browser-level and API/integration coverage.

### F28 — Production Configuration & Deployment QA

Production API configuration, frontend environment configuration, CORS, authentication/token configuration, production build verification, deployment smoke tests, real-role permission verification, migration verification, secret/configuration review, final security/configuration QA.

## 13. Deferred Business Rules

These are intentionally deferred pending input from business/accounting owners, not unfinished bugs:

- **F25 — Accounting Classification / Finance Verification Enhancement.** The current employee-facing category → AccountChart mapping is an MVP mechanism. Deeper Finance rules (e.g. the correct accounting treatment for IT equipment/laptops) need confirmation from the accounting/business owners rather than being guessed in software.
- **F26 — Request-on-Behalf Workflow.** Intentionally separated from the core requester workflow because it introduces additional authorization, audit, identity, and accountability questions that haven't been resolved yet.
- **F27 — Expanded Reviewer Notification Coverage.** Additional notifications for intermediate approval stages (Department Head, Accounts, GM, Director) may be added later. The current implementation does not invent notification behavior beyond what the backend already supports (§7).

## 14. Recommended Next Implementation Step

Start F23 (Procurement Processing) as a frontend-only slice against the existing `/process/` endpoint and `pending-procurement` scope, following the same pattern as the GM/Director pages (queue page, shared `PurchaseRequestDetail`, action dialog, reviewer-access hook, sidebar entry). Confirm the two open business questions above (supplier/PO capture, decline path) with stakeholders before or during that work, since they would require backend changes if answered "yes."

## 15. Handoff Notes

- Branch: `forms/purchase-requisition`, based on `main`.
- Seeded test accounts (`python manage.py seed_pr_test_data`, idempotent): Requester, Department Head, Accounts, General Manager, Director, and Procurement Officer, one per stage, each with only the permissions that stage needs.
- Frontend tests: `cd employee-portal && npx vitest run`. Backend tests: from the repository root's virtual environment, `pytest` inside `erp_project` (Django settings via `erp_project/.env`, not committed).
- The `PurchaseRequestDetail` component and `statusConfig.ts` helpers (`getStageInfo`, `lastMatch`) are shared across every requester and reviewer view — changes there affect all stages at once, by design.
- No backend files were changed for F22 (Director approval) or its ScrollArea follow-up fix; both are frontend-only.

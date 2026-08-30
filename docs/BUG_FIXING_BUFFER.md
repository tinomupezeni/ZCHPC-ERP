# Bug Fixing Buffer & Protocol

This document defines the process for managing, identifying, and resolving bugs within ZCHPC ERP. It acts as the standard operating procedure (SOP) for utilizing the "Bug Fixing Buffer" during sprints.

## 1. The Bug Fixing Buffer Concept

In Agile sprints, a specific time buffer (e.g., 15-20% of sprint capacity) is allocated strictly for unforeseen bugs, production hotfixes, and technical debt resolution. 
- **P0 / P1 Bugs**: Addressed immediately, superseding active feature development.
- **P2 / P3 Bugs**: Added to the backlog and scheduled into the buffer time of the current or next sprint.

---

## 2. Mandatory Debugging Protocol

When a bug is reported, developers must follow this strict diagnostic protocol before writing any code:

### Step 1: Parse the Error
- Identify the exact HTTP Status Code (e.g., 400, 403, 404, 500).
- Identify the exact API Endpoint and HTTP Method.
- Capture the raw error message or stack trace.

### Step 2: Consult the Knowledge Base (KB)
- Check `kb/KB_INDEX.json` and linked files.
- Understand the context of the error based on historical documentation.

### Step 3: Check P0 Causes (Golden Rules)
Many bugs stem from known architectural pitfalls. Always check:
- **Case Mismatches**: Is the frontend sending `camelCase` to a backend expecting `snake_case`?
- **OneToOne Relation Failures**: Are you using `getattr(user, 'profile', None)`? **Stop.** Use a `try-except` block to catch `DoesNotExist`.
- **Type Mismatches**: Are you calling `.strip()` on a UUID object? Convert it first using `str(uuid_obj)`.
- **Permissions**: `403 Forbidden`? Check the custom `RBACMiddleware` before looking at DRF permissions. `IsAdminUser` checks `is_staff`, not `is_superuser`.
- **404 Errors**: Ensure the endpoint is registered in `urls.py` AND exported properly in `views/__init__.py`.

### Step 4: Trace and Verify
Follow `AI_DEBUGGING_METHODOLOGY.md`. **Never assume the cause—verify by reading the actual code.** Trace the payload from the Frontend Service -> Backend URL -> View -> Service/Command -> Repository -> Model.

---

## 3. Surgical Edits & Code Standards

- **Targeted Fixes**: When resolving a bug, make *surgical* edits. Do not refactor unrelated code in the same PR.
- **Testing Verification**: Every fix MUST be verified. You must either write a unit/integration test that covers the bug or provide a reproduction script that demonstrates the fix.

---

## 4. Post-Fix Procedure

1. **Update Documentation**: If a new class of bug is discovered, document the solution in the Knowledge Base or `GEMINI.md`.
2. **Review Metrics**: Track time spent in the Bug Fixing Buffer to adjust resource allocation for future sprints.

# ZCHPC ERP - Gemini CLI Guidelines

This document serves as the foundational mandate for Gemini CLI when operating within the ZCHPC ERP project. It consolidates project-specific "Golden Rules," architectural patterns, and standard operating procedures (SOPs).

## 1. Project Architecture & Stack

### Backend (Django REST Framework)
- **Location:** `erp_project/`
- **Pattern:** Clean Architecture with Repository Pattern.
- **Key Files:**
  - Models: `erp_project/src/modules/*/models.py`
  - Repositories: `erp_project/src/modules/*/repositories/`
  - Views: `erp_project/src/modules/*/views/`
  - URLs: `erp_project/src/modules/*/urls.py`
- **Database:** PostgreSQL (Production/Dev), SQLite (Local/Testing).

### Frontend (React + Vite + TypeScript)
- **Locations:** `employee-portal/` and `zchpc-erp-synergy-main/`
- **Styling:** Vanilla CSS (preferred) / Tailwind CSS.
- **Key Files:**
  - Services (API calls): `src/services/`
  - Components: `src/components/`
  - Pages: `src/pages/`

---

## 2. Standard Operating Procedures (SOPs)

### 2.1 Debugging Protocol (MANDATORY)
1. **Parse Error:** Identify HTTP Status, Endpoint, and exact Error Message.
2. **Consult KB:** Refer to `kb/KB_INDEX.json` and its linked files (`400`, `403`, `404`, `500`, `migrations`).
3. **P0 First:** Check for most common causes (e.g., camelCase vs snake_case, OneToOne reverse relation failures).
4. **Follow `AI_DEBUGGING_METHODOLOGY.md`:** Trace from error to root cause. **Never assume - verify by reading code.**

### 2.2 Backend Changes
- **Models:** Always check if a field change requires updates in the **Repository**, **Domain Entity**, and **Value Objects**.
- **Migrations:**
  - Use `RunPython` for data cleanup before schema changes (e.g., fixing invalid UUIDs).
  - Drop incompatible PostgreSQL indexes (like `varchar_pattern_ops`) before changing field types.
- **Tests:** Run `pytest` after any backend change.

### 2.3 Frontend Changes
- **API Integration:** Ensure field names match the backend's `snake_case` or the frontend service's mapping logic.
- **Styling:** Adhere to existing component patterns in `src/components/ui/`.

---

## 3. Standard Commands

### Backend (from `erp_project/`)
- **Run Tests:** `pytest` (or `pytest <path_to_test>`)
- **Apply Migrations:** `python manage.py migrate`
- **Make Migrations:** `python manage.py makemigrations`
- **Start Server:** `python manage.py runserver`

### Frontend (from `employee-portal/` or `zchpc-erp-synergy-main/`)
- **Install Deps:** `npm install`
- **Start Dev:** `npm run dev`
- **Build:** `npm run build`
- **Lint:** `npm run lint`

---

## 4. Hard-Learned Lessons (Golden Rules)

- **OneToOne Relations:** `getattr(user, 'profile', None)` DOES NOT catch `DoesNotExist`. Use a `try-except` block.
- **Type Mismatches:** UUID objects in models do not have `.strip()`. Convert to `str(uuid_obj)` in Value Objects if needed.
- **Permissions:** `IsAdminUser` checks `is_staff`, not `is_superuser`.
- **RBAC:** Custom `RBACMiddleware` runs before DRF permissions; check it first for `403` errors.
- **404 Errors:** Verify if the endpoint is actually registered in the backend `urls.py` and exported in `views/__init__.py`.

---

## 5. Coding Standards
- **Backend:** `snake_case` for all Python variables, fields, and functions.
- **Frontend:** `camelCase` for TypeScript/React, except when matching backend API payloads.
- **Surgical Edits:** Use `replace` for targeted changes. Do not refactor unrelated code.
- **Verification:** Every fix MUST be verified either by a reproduction script or by running the relevant test suite.

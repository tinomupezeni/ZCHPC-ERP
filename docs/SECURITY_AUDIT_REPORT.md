# Security Audit & Remediation Report: ZCHPC ERP Backend

**Date:** 2026-08-26  
**Scope:** Secrets Management, Fail-Open Vulnerabilities, CORS/DEBUG Defaults, RBAC Middleware, Deployment Configuration  
**Status:** Core fixes implemented and committed · Regression tests added · Architectural flags documented for senior review

---

## 1. Executive Summary

As part of my onboarding and initial codebase review, I conducted a security audit of the Django backend settings, custom middleware, and Docker/Nginx deployment configuration.

I identified and patched several **fail-open vulnerabilities** where the system would silently grant access or fall back to insecure defaults when environment variables or authentication tokens were missing. I also mapped the Clean Architecture structure (`src/modules/`), traced the request flow through the middleware chain, and added a regression test suite to ensure these security baselines are maintained.

---

## 2. Implemented Fixes

### 2.1. Settings & Configuration (`settings.py`)

*   **Removed Hardcoded Secrets:** Eliminated hardcoded fallbacks for `SECRET_KEY` and `DB_PASSWORD`. The application now raises `ImproperlyConfigured` on startup if these are missing, rather than running with known insecure defaults.
*   **Locked DEBUG Default:** `DEBUG` now defaults to `False`. It must be explicitly enabled via environment variable for local development.
*   **Locked CORS Defaults:**
    *   `CORS_ALLOW_ALL_ORIGINS` now defaults to `False`.
    *   `CORS_ALLOW_CREDENTIALS` now defaults to `False` (the frontend uses JWT in the `Authorization` header, not cross-origin cookies).
*   **Global DRF Permissions:** Added `rest_framework.permissions.IsAuthenticated` to `DEFAULT_PERMISSION_CLASSES`. Previously, DRF defaulted to `AllowAny`, meaning any API view lacking explicit permission classes was accidentally public.

### 2.2. RBAC Middleware Hardening (`middleware.py`)

Rewrote `RBACMiddleware` to enforce a strict **fail-closed** security model:

*   **Authentication Enforcement:** Unauthenticated requests to `/api/` now immediately return `401 Unauthorized` at the middleware layer, rather than being passed down to the view.
*   **URL Resolution Safety:** If `django.urls.resolve()` fails to map a path to a known view/permission, the middleware now returns `403 Forbidden` instead of silently allowing the request through.
*   **Role Fallback Safety:** If the system cannot determine a user's role (e.g., missing employee profile), it now denies access (`403`) instead of silently assigning a default role.
*   **Media Protection Baseline:** Added routing to require authentication for `/media/` requests at the middleware layer. *(Note: see Flag #1 for the Nginx-layer limitation.)*

### 2.3. Hardcoded Temporary Password (`user_service.py`)

*   **File:** `src/modules/identity/application/services/user_service.py`
*   **Issue:** A default temporary password (`password`) was hardcoded in source code and assigned to newly created users. This meant every new account started with the same, publicly-known password.
*   **Fix:** Replaced with a `generate_temp_password()` function using Python's `secrets` module, ensuring each user receives a unique, cryptographically secure temporary password. This is consistent with the existing `AttendanceQRToken.generate_token()` pattern already in the codebase.

### 2.4. Environment Template Cleanup (`.env.example`)

*   Replaced realistic-looking placeholder credentials (`password`) with obviously fake values (`CHANGE_ME_TO_A_STRONG_PASSWORD`) so developers and security scanners can clearly distinguish templates from real credentials.

### 2.5. Regression Testing (`test_security.py`)

Created a test suite to prevent these vulnerabilities from being reintroduced:

*   Verification of locked `DEBUG` and `CORS` defaults.
*   Verification of DRF global `IsAuthenticated` default.
*   Rejection of anonymous API requests (`401`).
*   Rejection of invalid JWT tokens (`401`).
*   Rejection of authenticated users lacking RBAC permissions (`403`).
*   Verification that public endpoints (`/api/v2/health/`, `/static/`) remain accessible.
*   Verification that unauthenticated `/media/` requests are rejected.

---

## 3. Challenges & Architectural Discoveries

### 3.1. Testing Middleware vs. DRF Views

**Challenge:** Initial tests using DRF's `force_authenticate()` returned `401` because that helper only mocks authentication at the *View* layer, bypassing our custom `JWTAuthenticationMiddleware` and `RBACMiddleware`.
**Solution:** Refactored tests to generate real JWT tokens using `AccessToken.for_user(user)` and inject them via `client.credentials(HTTP_AUTHORIZATION=...)`. This ensures the entire middleware chain is tested exactly as it behaves in production.

### 3.2. Domain vs. Infrastructure Role Mapping

**Challenge:** Attempting to assign a `role` directly to `CustomUser` in tests threw a `ValueError` (field does not exist).
**Discovery:** Explored the Clean Architecture domain layer (`modules/identity/domain/entities/role.py`) and infrastructure models. Confirmed that `CustomUser` does not hold the role directly; it is resolved via the `Employee` OneToOne relationship (`request.user.employee_profile.role`). Updated the middleware and tests to respect this data model.

### 3.3. The Dual JWT Architecture

**Observation:** The project has both a custom `JWTAuthenticationMiddleware` and DRF's `JWTAuthentication` class.
**Understanding:** This is intentional defense-in-depth. The custom middleware sets `request.user` for non-DRF Django views and internal logic; DRF's authentication class handles APIViews. Both are now backed by the fail-closed RBAC layer.

---

## 4. Critical Flags for Senior Review (Action Required)

While auditing the deployment layer (`nginx.conf`, `docker-compose.yml`), I identified architectural issues that require senior/DevOps intervention, as they sit outside the scope of my middleware fixes.

### 🚨 Flag 1: Nginx Bypasses Django for `/media/` Files (High Priority)

**The Issue:** `nginx.conf` serves `/media/` directly from the Docker volume using `alias /app/mediafiles/`.
**The Risk:** Because Nginx handles the request, it **bypasses Django entirely**. My middleware fix to protect `/media/` routes is currently ineffective. An anonymous user who guesses a URL like `/media/resumes/john_doe.pdf` will be served the file by Nginx with no JWT or RBAC check.
**Proposed Fix:**
1. Change `nginx.conf` to `proxy_pass` `/media/` requests to the Django upstream.
2. Create a custom Django View (e.g., `ProtectedMediaView`) that verifies the JWT, checks **object-level permissions** (ensuring users can only download their *own* payslips/documents), and streams the file via `FileResponse`.
3. *I deliberately did not implement this on day one to avoid breaking the current media serving pipeline. Flagging for whoever owns deployment infrastructure.*

### ⚠️ Flag 2: Docker Compose Service Name Mismatch

**The Issue:** `nginx.conf` upstream points to `server api:8000;`, but `docker-compose.yml` names the Django service `web`.
**The Risk:** Nginx will fail to resolve the internal Docker DNS name `api`, resulting in `502 Bad Gateway` errors.
**Proposed Fix:** Update the Nginx upstream to `server web:8000;`.

### ⚠️ Flag 3: Docker Compose "Fail-Open" Secret Fallbacks

**The Issue:** The compose file uses bash fallback syntax: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-erp@1234}`.
**The Risk:** If a `.env` variable is missing, Docker silently deploys the database with the weak default password.
**Proposed Fix:** Change `:-` to `:?` (e.g., `${POSTGRES_PASSWORD:?DB password required}`). This forces Docker Compose to crash on startup if the secret is not explicitly provided.

### ⚠️ Flag 4: Production Domains Missing in `.env` Template

**The Issue:** The provided `.env` template only lists `localhost` for `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
**The Risk:** Deploying to production (`zchpcerp.zchpc.ac.zw`) will result in Django throwing `400 Bad Request` errors and the React frontend failing due to CORS blocks.
**Proposed Fix:** Update `.env.example` to include the production domains as documented examples.

### ⚠️ Flag 5: Git History Still Contains Old Secrets

**The Issue:** The old hardcoded secrets remain in the Git commit history even though they are removed from the current code.
**The Risk:** Anyone with repo access can retrieve the old credentials from history.
**Proposed Fix:** Coordinate a team-wide effort to use `git filter-repo` or BFG Repo-Cleaner to scrub history, followed by a force-push. *(Not performed solo to avoid disrupting teammates' branches.)*

---

## 5. Secret Rotation Checklist

- [x] **Identify exposed secrets:** `SECRET_KEY`, `DB_PASSWORD`, `DEFAULT_TEMP_PASSWORD`.
- [x] **Generate new secure keys** via `get_random_secret_key()` and `openssl rand`.
- [x] **Update local `.env`** with new values.
- [x] **Replace hardcoded temp password** with `secrets`-based random generation.
- [x] **Commit secure code** removing all fallbacks.
- [ ] **Rotate Database Password** in the live Postgres container: `ALTER USER erp_user WITH PASSWORD '<new>';`
- [ ] **Update Production/Staging `.env`:** *(Requires DevOps coordination)*
- [ ] **Purge Git History:** *(Requires team coordination — see Flag #5)*

---

## 6. Next Steps

1. Review the `test_security.py` suite and integrate it into the CI/CD pipeline.
2. Schedule a sync to discuss the **Nginx Media Bypass (Flag #1)** and assign implementation of the `ProtectedMediaView`.
3. Coordinate the Git history purge (Flag #5) with the team.
4. Continue onboarding into the Application/Use-Case layer of the Clean Architecture to begin contributing to business logic features.
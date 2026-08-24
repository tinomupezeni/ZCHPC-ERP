# QA & Test Hardening Cycle

Quality Assurance (QA) and test hardening are critical to maintaining the stability of the ZCHPC ERP system. This document outlines the mandatory testing cycle, from local development to production deployment.

## 1. Test Architecture

The `erp_project/tests/` directory is structured to support different testing scopes:
- `unit/`: Tests individual functions, Domain Entities, and Value Objects in isolation.
- `integration/`: Tests the Application layer, Repositories, and cross-module interactions (Providers).
- `e2e/`: Tests full API endpoints (Views/Serializers) mimicking real client requests.

### Coverage Targets
- **Domain Layer**: 95%+ coverage (Core business logic).
- **Application Layer**: 90%+ coverage.
- **Infrastructure Layer**: 80%+ coverage.
- **API Layer**: 100% contract testing.

---

## 2. Local QA Cycle (Developer Phase)

Before any code is committed, developers must adhere to the following hardening steps:

### 2.1 Static Analysis & Linting
- **Backend**: Code must follow `snake_case` conventions. Maximum file size is strictly **400 lines**.
- **Frontend**: Code must follow `camelCase` conventions. `npm run lint` must pass with zero errors.

### 2.2 Local Test Execution
- Developers must run `pytest` locally.
- For targeted fixes, run specific module tests: `pytest src/modules/<module_name>/tests/`.
- **Database Hygiene**: Migrations must be tested locally. Run `python manage.py makemigrations` and `python manage.py migrate`. If schema changes involve data cleanup (e.g., UUID casting), a `RunPython` data migration must be verified.

---

## 3. Automated CI/CD QA Pipeline

Upon pushing to the `main` branch (or submitting a Pull Request), the GitHub Actions pipeline enforces the following:

1. **Build Verification**: Ensures Docker images for the API, Admin Frontend, and Portal build successfully without dependency resolution errors.
2. **Automated Test Suite**: (To be enforced) Runs the complete `pytest` suite and frontend test scripts. A failure here blocks deployment.
3. **Configuration Check**: Validates that critical environment variables (e.g., `VITE_API_URL_MAIN`) are correctly injected during the build.

---

## 4. Hardening and Regression

### 4.1 Bug Verification
Every bug fix must be accompanied by a reproduction script or a dedicated test case that previously failed and now passes. This prevents regression.

### 4.2 Security & Permissions Hardening
- **RBAC Checks**: Tests must explicitly verify that endpoints reject requests from unauthorized roles (testing the `RBACMiddleware`).
- **Data Isolation**: Tests must ensure that employees can only view their own data in the portal, while admins can view organizational data based on their clearance.

### 4.3 Database Hardening
- Validate that `OneToOne` relationships handle `DoesNotExist` exceptions gracefully.
- Ensure UUIDs are properly cast to strings (`str(uuid_obj)`) before serialization.

---

## 5. Release Approval

A feature or release is considered "hardened" when:
1. All unit, integration, and E2E tests pass.
2. The CI pipeline completes a successful build.
3. A peer code review confirms adherence to Clean Architecture and the 400-line limit.
4. UAT (User Acceptance Testing) is signed off (See `USER_ACCEPTANCE_TESTING.md`).

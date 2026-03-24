# ZCHPC ERP Dockerization Journey

This document chronicles the complete process of Dockerizing the ZCHPC ERP system, including all errors encountered and their solutions.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Phase 1: Initial Dockerization](#phase-1-initial-dockerization)
3. [Phase 2: Frontend Discovery & Dockerization](#phase-2-frontend-discovery--dockerization)
4. [Phase 3: Build & Push Scripts](#phase-3-build--push-scripts)
5. [Phase 4: Domain Configuration](#phase-4-domain-configuration)
6. [Phase 5: Deployment Configuration](#phase-5-deployment-configuration)
7. [Errors & Solutions](#errors--solutions)
8. [Final Architecture](#final-architecture)

---

## Project Overview

**System Components:**
- **Backend API**: Django 5.2.8 with Django REST Framework
- **Main ERP Frontend**: React/Vite application (`zchpc-erp-synergy-main`)
- **Employee Portal**: React/Vite application (`employee-portal`)
- **Database**: PostgreSQL 16

**Production Domains:**
- Main ERP: `https://zchpcerp.zchpc.ac.zw`
- Employee Portal: `https://employees.zchpc.ac.zw`

**Docker Hub Repository:** `tinotenda762`

---

## Phase 1: Initial Dockerization

### Files Created

#### 1. `erp_project/Dockerfile`
Multi-stage build for the Django API:
- Stage 1 (Builder): Installs dependencies in virtual environment
- Stage 2 (Production): Slim image with only runtime dependencies

#### 2. `erp_project/entrypoint.sh`
Startup script that:
- Waits for PostgreSQL to be ready
- Runs database migrations
- Collects static files
- Creates superuser (if configured)
- Starts Gunicorn server

#### 3. `erp_project/.dockerignore`
Excludes unnecessary files from Docker context.

#### 4. Health Check Endpoint
Added `/api/v2/health/` endpoint for container health monitoring.

---

## Phase 2: Frontend Discovery & Dockerization

Discovered two frontend applications that needed containerization:

### Employee Portal (`employee-portal/Dockerfile`)
```dockerfile
FROM node:22-alpine AS deps
# ... dependencies stage

FROM node:22-alpine AS builder
# Build with VITE_API_URL

FROM nginx:alpine AS production
# Serve with nginx
```

### Main ERP Frontend (`zchpc-erp-synergy-main/Dockerfile`)
```dockerfile
FROM node:20-alpine AS deps
# ... dependencies stage

FROM node:20-alpine AS builder
# Build with VITE_API_URL

FROM nginx:alpine AS production
# Serve with nginx
```

Both frontends use nginx to serve the built static files.

---

## Phase 3: Build & Push Scripts

### PowerShell Script (`build-and-push.ps1`)
For Windows development machines:
```powershell
# Builds all three images
# Tags with 'latest' and date-based tags
# Pushes to Docker Hub
```

### Bash Script (`build-and-push.sh`)
For Linux/Mac machines with same functionality.

---

## Phase 4: Domain Configuration

### Updated Files:
1. **Django Settings** (`erp_root/settings.py`):
   - `ALLOWED_HOSTS`: Added production domains
   - `CORS_ALLOWED_ORIGINS`: Added frontend domains
   - `CSRF_TRUSTED_ORIGINS`: Added production domains

2. **Frontend Environment Files**:
   - `employee-portal/.env.production`
   - `zchpc-erp-synergy-main/.env.production`

Both set `VITE_API_URL=https://zchpcerp.zchpc.ac.zw`

---

## Phase 5: Deployment Configuration

### `deploy/` Directory Structure
```
deploy/
├── docker-compose.yml    # Production compose file
├── .env                  # Environment variables
└── README.md            # Deployment instructions
```

### docker-compose.yml
```yaml
services:
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"

  api:
    image: tinotenda762/zchpc-erp-api:latest
    ports:
      - "0.0.0.0:8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    image: tinotenda762/zchpc-erp-frontend:latest
    ports:
      - "0.0.0.0:3000:80"

  portal:
    image: tinotenda762/zchpc-erp-portal:latest
    ports:
      - "0.0.0.0:3001:80"
```

---

## Errors & Solutions

### Error 1: Modal Import Case Sensitivity

**Error Message:**
```
Could not load /app/src/components/ui/Modal
```

**Cause:**
Linux containers are case-sensitive. Files were named `modal.tsx` but imports used `Modal`.

**Solution:**
Changed imports in 4 training-related files:
```typescript
// Before
import { Modal } from '@/components/ui/Modal';

// After
import { Modal } from '@/components/ui/modal';
```

**Files Fixed:**
- `src/components/HR/training/TrainingForm.tsx`
- `src/components/HR/training/EnrollmentDialog.tsx`
- `src/components/HR/training/TrainingList.tsx`
- `src/components/HR/training/TrainingDetails.tsx`

---

### Error 2: Dockerfile Casing Warning

**Warning:**
```
FromAsCasing: 'as' and 'FROM' keywords' casing do not match
```

**Solution:**
```dockerfile
# Before
FROM python:3.12-slim as builder

# After
FROM python:3.12-slim AS builder
```

---

### Error 3: JobsListPage Undefined Error

**Error Message:**
```
Uncaught TypeError: Cannot read properties of undefined (reading 'length')
```

**Cause:**
Backend API returns array `[]` directly, but frontend expected `{ jobs: [] }` format.

**Solution:**
Updated `employee-portal/src/pages/JobsListPage.tsx`:
```typescript
const loadJobs = async () => {
  try {
    setIsLoading(true);
    const response = await jobsService.getJobs();
    // Handle both array response and { jobs: [] } response
    const jobsList = Array.isArray(response) ? response : (response.jobs || []);
    setJobs(jobsList);
  } catch (error) {
    // ...
  }
};
```

---

### Error 4: Hardcoded API URLs (Connection Refused)

**Error Message:**
```
POST http://127.0.0.1:8000/api/auth/token/ net::ERR_CONNECTION_REFUSED
```

**Cause:**
Multiple files had hardcoded localhost URLs instead of using environment variables.

**Files with Hardcoded URLs:**

1. **`zchpc-erp-synergy-main/src/services/api.tsx`**
```typescript
// Before
export const API_BASE_URL = "http://127.0.0.1:8000/api/";
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

// After
const API_URL = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = `${API_URL}/api/`;
const api = axios.create({
  baseURL: `${API_URL}/api`,
});
```

2. **Report Files** (6 files in `src/components/HR/reports/`):
   - `AllowancesReport.tsx`
   - `DeductionsReport.tsx`
   - `NSSAReport.tsx`
   - `PAYEReport.tsx`
   - `LeaveBalanceReport.tsx`
   - `BasicSalaryReport.tsx`

```typescript
// Before
fetch("http://localhost:8000/api/allowances/")

// After
const API_URL = import.meta.env.VITE_API_URL || '';
fetch(`${API_URL}/api/allowances/`)
```

3. **Employee Portal Services:**
   - `src/services/jobs.service.ts`
   - `src/services/attendance.service.ts`

---

### Error 5: Dockerfile Environment Variable Override

**Error Message:**
```
POST https://employees.zchpc.ac.zw/portal/auth/login/ 405 (Method Not Allowed)
```

**Cause:**
Dockerfiles had default fallback to `localhost:8000` which overrode `.env.production`:
```dockerfile
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:8000}
```

**Solution:**
Updated both frontend Dockerfiles:
```dockerfile
# Before
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:8000}

# After
ARG VITE_API_URL=https://zchpcerp.zchpc.ac.zw
ENV VITE_API_URL=${VITE_API_URL}
```

---

### Error 6: LeaveBalanceService Import Error

**Error Message:**
```
ImportError: cannot import name 'LeaveBalanceService' from
'modules.leave.application.services'
```

**Cause:**
The `__init__.py` file in `src/modules/leave/application/services/` was empty.

**Solution:**
Created proper exports in `services/__init__.py`:
```python
from modules.leave.application.services.leave_balance_service import (
    LeaveBalanceService,
    # ... other exports
)
from modules.leave.application.services.leave_provider import LeaveProvider
from modules.leave.application.services.leave_request_service import (
    LeaveRequestService,
    # ... other exports
)
from modules.leave.application.services.leave_type_service import (
    LeaveTypeService,
    # ... other exports
)

__all__ = [
    "LeaveBalanceService",
    "LeaveRequestService",
    "LeaveTypeService",
    "LeaveProvider",
    # ... other exports
]
```

---

### Error 7: shared_kernel Module Not Found

**Error Message:**
```
ModuleNotFoundError: No module named 'shared_kernel'
```

**Cause:**
The `src` directory wasn't in Python's module search path. The project structure:
```
erp_project/
├── src/
│   ├── modules/
│   └── shared_kernel/
├── manage.py
└── erp_root/
```

**Solution:**
Added `PYTHONPATH` to Dockerfile:
```dockerfile
# Before
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# After
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    APP_HOME=/app
```

---

## Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    cPanel Reverse Proxy                          │
│  zchpcerp.zchpc.ac.zw  →  10.50.14.12:3000 (frontend)           │
│  zchpcerp.zchpc.ac.zw/api  →  10.50.14.12:8000 (api)            │
│  employees.zchpc.ac.zw  →  10.50.14.12:3001 (portal)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VM (10.50.14.12)                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Docker Compose                            ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         ││
│  │  │  Frontend   │  │   Portal    │  │     API     │         ││
│  │  │  (nginx)    │  │  (nginx)    │  │  (gunicorn) │         ││
│  │  │  :3000      │  │  :3001      │  │  :8000      │         ││
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘         ││
│  │                                           │                 ││
│  │                                    ┌──────▼──────┐         ││
│  │                                    │  PostgreSQL │         ││
│  │                                    │    :5432    │         ││
│  │                                    └─────────────┘         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Commands

### Build and Push (Windows)
```powershell
cd C:\Users\Dell\Documents\projects\ZCHPC-ERP
.\build-and-push.ps1
```

### Deploy on VM
```bash
cd ~/Documents/deploy

# Pull latest images
docker compose pull

# Start services
docker compose up -d

# View logs
docker logs -f zchpc_api
docker logs -f zchpc_frontend
docker logs -f zchpc_portal

# Restart a service
docker compose restart api
```

### Environment Variables (`.env`)
```env
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=<strong-password>
SECRET_KEY=<random-secret-key>
ADMIN_EMAIL=admin@zchpc.ac.zw
ADMIN_PASSWORD=<admin-password>
IMAGE_TAG=latest
```

---

### Error 8: Wrong Module Name (shared_kernel vs shared)

**Error Message:**
```
ModuleNotFoundError: No module named 'shared_kernel'
```

**Cause:**
The actual directory was named `shared` but code was importing from `shared_kernel`.

**Directory Structure:**
```
erp_project/src/
├── modules/
│   ├── leave/
│   └── recruitment/
└── shared/          <-- Actual name
    ├── domain/
    │   ├── base/
    │   └── exceptions/
    └── infrastructure/
```

**Solution:**
Fixed all imports in 11 files from `shared_kernel` to `shared`:

```python
# Before
from shared_kernel.domain.exceptions import NotFoundError, ValidationError
from shared_kernel.domain.base import AggregateRoot

# After
from shared.domain.exceptions import NotFoundError, ValidationError
from shared.domain.base import AggregateRoot
```

**Files Fixed:**
- `modules/leave/application/services/leave_balance_service.py`
- `modules/leave/application/services/leave_type_service.py`
- `modules/leave/application/services/leave_request_service.py`
- `modules/recruitment/domain/value_objects/recruitment.py`
- `modules/recruitment/domain/events/recruitment_events.py`
- `modules/recruitment/domain/services/recruitment_services.py`
- `modules/recruitment/domain/entities/job.py`
- `modules/recruitment/domain/entities/candidate.py`
- `modules/recruitment/domain/entities/application.py`
- `modules/recruitment/application/services/job_service.py`
- `modules/recruitment/application/services/application_service.py`

---

### Error 9: Django Can't Find Models (CustomUser not installed)

**Error Message:**
```
django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model
'identity.CustomUser' that has not been installed
```

**Cause:**
Django looks for models in `<app>/models.py` or `<app>/models/__init__.py`. The project structure had models in `<app>/infrastructure/persistence/models.py`, which Django doesn't automatically discover.

**Solution:**
Created root `models.py` files in each module that re-export models from the infrastructure layer:

```python
# modules/identity/models.py
from modules.identity.infrastructure.persistence.models import (
    AuditLog,
    CustomUser,
    CustomUserManager,
)

__all__ = ["CustomUser", "CustomUserManager", "AuditLog"]
```

**Files Created:**
- `src/modules/identity/models.py`
- `src/modules/hr/models.py`
- `src/modules/attendance/models.py`
- `src/modules/leave/models.py`
- `src/modules/recruitment/models.py`
- `src/modules/payroll/models.py`
- `src/modules/accounts/models.py`
- `src/modules/procurement/models.py`
- `src/modules/portal/models.py`

---

## Local Development & Debugging

### Local Docker Compose Setup

Created `docker-compose.local.yml` for debugging before production deployment.

**Run Locally (PowerShell):**
```powershell
# Start everything
.\run-local.ps1

# View logs
.\run-local.ps1 -Logs

# View specific service logs
.\run-local.ps1 -Logs -Service api

# Stop everything
.\run-local.ps1 -Down

# Clean up (remove volumes and images)
.\run-local.ps1 -Clean

# Rebuild from scratch
.\run-local.ps1 -Build
```

**Run Locally (Bash):**
```bash
# Start everything
./run-local.sh

# View logs
./run-local.sh --logs

# View specific service logs
./run-local.sh --logs --service api

# Stop everything
./run-local.sh --down

# Clean up
./run-local.sh --clean
```

**Local URLs:**
| Service | URL |
|---------|-----|
| Main ERP | http://localhost:3000 |
| Employee Portal | http://localhost:3001 |
| API | http://localhost:8000 |
| API Health | http://localhost:8000/api/v2/health/ |
| Django Admin | http://localhost:8000/admin/ |

**Default Credentials:**
- Email: `admin@local.dev`
- Password: `admin123`

---

## Lessons Learned

1. **Case Sensitivity**: Linux containers are case-sensitive; Windows is not. Always match exact casing in imports.

2. **Environment Variables in Vite**: Vite bakes environment variables at build time. Docker ENV variables override `.env` files.

3. **Python Path in Docker**: When using a `src/` directory structure, explicitly set `PYTHONPATH`.

4. **API Response Formats**: Always handle multiple response formats in frontend code for flexibility.

5. **Module Exports**: Python packages need proper `__init__.py` files with explicit exports.

6. **Health Checks**: Always include health check endpoints for container orchestration.

---

## Quick Reference

| Service | Port | Image |
|---------|------|-------|
| API | 8000 | tinotenda762/zchpc-erp-api |
| Frontend | 3000 | tinotenda762/zchpc-erp-frontend |
| Portal | 3001 | tinotenda762/zchpc-erp-portal |
| Database | 5432 | postgres:16-alpine |

---

*Document created: March 2026*
*Last updated: March 2026*

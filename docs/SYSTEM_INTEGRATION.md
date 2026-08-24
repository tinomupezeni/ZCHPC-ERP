# System Integration Guide

This document outlines how the different components of the ZCHPC ERP system integrate, covering backend services, frontend applications, external dependencies, and deployment environments.

## 1. High-Level Architecture Overview

ZCHPC ERP operates on a **Modular Monolith** architecture, consisting of three main applications integrated via HTTP REST APIs:
1. **Django Backend (`erp_project`)**: Port 8000. Provides the core REST API for all business logic.
2. **ERP Admin Frontend (`zchpc-erp-synergy-main`)**: Port 5173. React-based management dashboard for HR, Payroll, and Accounting.
3. **Employee Portal (`employee-portal`)**: Port 5174. React-based self-service portal for employees.

These systems rely on a shared **PostgreSQL** database and are served in production via **Nginx** reverse proxies.

---

## 2. Frontend to Backend Integration

### 2.1 API Communication
- All frontend applications communicate with the backend exclusively via the `/api/v2/*` REST endpoints.
- **Protocol**: HTTPS (Production), HTTP (Local).
- **Data Format**: JSON payloads.
- **Client**: Both React applications utilize `Axios` for HTTP requests, integrated with `React Query` for state management and caching.

### 2.2 Authentication & Authorization
- **Token Mechanism**: Integration relies on `SimpleJWT`. The frontend receives an Access Token (valid for 24 hours) and a Refresh Token (valid for 30 days) upon successful login.
- **Transport**: Tokens are passed in the `Authorization: Bearer <token>` header for all protected API calls.
- **RBAC**: The backend enforces access via a custom `RBACMiddleware` before reaching Django REST Framework (DRF) view permissions. The frontend dynamically renders UI elements based on the roles embedded in the JWT or fetched from a `/me` endpoint.

---

## 3. Internal Backend Integration (Module-to-Module)

ZCHPC ERP enforces strict boundaries between its modules (e.g., HR, Payroll, Accounts).

### 3.1 The Provider Pattern
Modules do not directly query the database models of other modules. Instead, cross-module communication is handled via the **Provider Pattern**.
- **Example**: The Payroll module needs employee salary details. It calls an `IEmployeeProvider` interface, which is implemented by the HR module.
- **Benefit**: This decouples the domain layers, ensuring changes in HR's internal schema do not break Payroll logic.

### 3.2 Shared Kernel & Events
- **Domain Events**: Cross-cutting concerns are managed via an internal `event_bus.py`. When an entity changes state (e.g., `EmployeeTerminated`), a domain event is published. Subscribed modules (like Payroll or IT provisioning) can react asynchronously.

---

## 4. Database Integration

- **ORM**: The system integrates with PostgreSQL (v14+) using the Django ORM.
- **Repository Pattern**: Business logic never uses `Model.objects...` directly. Instead, infrastructure-layer Repositories implement domain-layer interfaces, mapping database records to pure Python Domain Entities and Value Objects.

---

## 5. Deployment & Infrastructure Integration

### 5.1 Docker & CI/CD
- GitHub Actions orchestrates the build process, creating Docker images for the Django API, Admin Frontend, and Employee Portal.
- Images are pushed to Docker Hub and pulled by the production VM.
- `docker-compose` is used to orchestrate the containers, linking the web services to the PostgreSQL container over a private Docker network.

### 5.2 Nginx Reverse Proxy
- Nginx sits at the edge, terminating SSL (via Certbot/Let's Encrypt).
- It routes traffic based on subdomains:
  - `api.your-domain.com` -> Gunicorn socket / Docker container (Backend)
  - `erp.your-domain.com` -> Admin Frontend static files
  - `portal.your-domain.com` -> Employee Portal static files

### 5.3 CORS Security
- `django-cors-headers` is strictly configured to only allow requests from the specific frontend origins (`VITE_API_URL_MAIN` and `VITE_API_URL_PORTAL`), preventing unauthorized cross-origin requests.

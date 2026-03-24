# Backend Refactoring Master Plan

## Modular Monolith Architecture

**Document Version:** 2.0
**Created:** March 2026
**Status:** Phase 11 Complete

---

## Current Status

All 11 phases have been completed. The system now operates as a **Modular Monolith**
with both legacy (v1) and new (v2) API endpoints running in parallel.

### Completed Phases

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Foundation | COMPLETE | Directory structure, shared kernel base |
| Phase 1: Shared Kernel | COMPLETE | Value objects, base classes, event bus |
| Phase 2: Identity Module | COMPLETE | User management, JWT auth |
| Phase 3: HR Core Module | COMPLETE | Employees, departments, positions |
| Phase 4: Attendance Module | COMPLETE | Time tracking, QR tokens |
| Phase 5: Leave Module | COMPLETE | Leave requests, balances |
| Phase 6: Recruitment Module | COMPLETE | Jobs, candidates, applications |
| Phase 7: Payroll Module | COMPLETE | Tax calculations, payslips |
| Phase 8: Accounts Module | COMPLETE | Chart of accounts, journals |
| Phase 9: Procurement Module | COMPLETE | Purchase requests, orders |
| Phase 10: Portal API | COMPLETE | Employee self-service portal |
| Phase 11: Final Cleanup | COMPLETE | Documentation, deprecation warnings |

### Architecture Decision

The legacy Django apps are **kept for database models only**:
1. They contain Django models (database tables) and migrations
2. New modules use these models through repository/provider patterns
3. All legacy views, serializers, and URL configs have been **deleted**
4. The v1 API has been **removed** - only v2 API endpoints exist now

What remains in legacy apps:
- `models.py` / `*_models.py` - Django models (database tables)
- `migrations/` - Database migrations
- `apps.py` - Django app configuration
- `middleware.py` (authentication only) - JWT and RBAC middleware
- `signals.py` (human_resources only) - Auto user creation
- `management/commands/` - Seeding and utility commands

All API endpoints are now at `/api/v2/*`

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the complete system documentation.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Principles](#architecture-principles)
3. [Code Standards](#code-standards)
4. [Target Structure](#target-structure)
5. [Module Designs](#module-designs)
6. [Implementation Phases](#implementation-phases)
7. [Timeline Summary](#timeline-summary)
8. [Risk Mitigation](#risk-mitigation)

---

## Project Overview

### Goal

Transform the current Django monolith into a well-structured modular monolith with clean architecture principles.

### Current State

- Tightly coupled Django apps
- Business logic scattered across views, serializers, and models
- No clear boundaries between modules
- Difficult to maintain and extend

### Target State

- Loosely coupled modules with clear boundaries
- Proper layering (domain, application, infrastructure, API)
- Each module independently testable
- Easy to understand and modify

### Migration Strategy

**Delete as we go.** Each module migration follows this pattern:

1. Build new module
2. Create adapter to bridge during transition
3. Migrate endpoints one by one
4. Delete old code immediately after each endpoint migrates
5. Module complete when all old code is gone

No parallel running of old and new. Clean cuts.

---

## Architecture Principles

### Dependency Rules

```
┌─────────────────────────────────────────────┐
│                 API Layer                    │
│         (Views, Serializers, Routes)         │
├─────────────────────────────────────────────┤
│             Application Layer                │
│      (Use Cases, Commands, Queries)          │
├─────────────────────────────────────────────┤
│               Domain Layer                   │
│   (Entities, Value Objects, Domain Services) │
├─────────────────────────────────────────────┤
│            Infrastructure Layer              │
│     (Repositories, External Services)        │
└─────────────────────────────────────────────┘

Dependencies point DOWNWARD only.
Domain layer has ZERO external dependencies.
```

### Module Communication

| Type | When to Use | Example |
|------|-------------|---------|
| Interface/Contract | Synchronous reads | Payroll gets employee salary from HR |
| Domain Events | Async reactions | PayrollProcessed triggers accounting entries |
| Shared Kernel | Common concepts | Money, DateRange value objects |

### Key Principles

1. **Single Responsibility** - Each class does one thing
2. **Dependency Inversion** - Depend on abstractions, not concretions
3. **Interface Segregation** - Small, focused interfaces
4. **Don't Repeat Yourself** - But don't over-abstract either
5. **Delete Aggressively** - Remove old code immediately after migration

---

## Code Standards

### File Size Limit

**Maximum 400 lines per file.** No exceptions.

If a file approaches 400 lines:
- Split into multiple files
- Extract classes or functions
- Create sub-modules

### File Organization

Each file should contain:
- One class (preferred), OR
- One set of closely related functions, OR
- One set of related constants/types

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module folder | lowercase, singular | `payroll/`, `hr/` |
| Python file | lowercase, underscore | `tax_calculator.py` |
| Class | PascalCase | `TaxCalculator` |
| Function/Method | lowercase, underscore | `calculate_paye()` |
| Constant | UPPERCASE, underscore | `MAX_TAX_RATE` |
| Private | Leading underscore | `_validate_input()` |

### Entity Naming

| Type | Convention | Example |
|------|------------|---------|
| Entity | Noun, singular | `Employee`, `Payslip` |
| Value Object | Descriptive noun | `Money`, `DateRange` |
| Domain Service | Verb + Noun | `TaxCalculator` |
| Application Service | Module + AppService | `PayrollAppService` |
| Command | Verb + Noun + Command | `ProcessPayrollCommand` |
| Query | Get + Noun + Query | `GetPayslipQuery` |
| Event | Noun + PastVerb | `PayrollProcessed` |
| Repository Interface | I + Entity + Repository | `IEmployeeRepository` |
| Repository Impl | Entity + Repository | `EmployeeRepository` |

### Testing Requirements

| Layer | Test Type | Coverage Target |
|-------|-----------|-----------------|
| Domain | Unit tests | 95%+ |
| Application | Integration tests | 90%+ |
| Infrastructure | Integration tests | 80%+ |
| API | Contract tests | 100% of endpoints |

### Documentation Requirements

- Every public class needs a docstring
- Every public method needs a docstring
- Complex logic needs inline comments
- Each module needs a README.md

---

## Target Structure

```
erp_project/
├── src/
│   ├── shared/                       # Shared Kernel
│   │   ├── domain/
│   │   │   ├── value_objects/
│   │   │   │   ├── money.py         # Money value object
│   │   │   │   ├── date_range.py    # Date range value object
│   │   │   │   ├── period.py        # Payroll period
│   │   │   │   └── ...
│   │   │   ├── base/
│   │   │   │   ├── entity.py        # Base entity class
│   │   │   │   ├── aggregate.py     # Aggregate root base
│   │   │   │   ├── value_object.py  # Value object base
│   │   │   │   └── domain_event.py  # Event base class
│   │   │   └── exceptions/
│   │   │       └── domain_exceptions.py
│   │   └── infrastructure/
│   │       ├── event_bus.py         # In-process event bus
│   │       ├── unit_of_work.py      # Transaction management
│   │       └── base_repository.py   # Repository base
│   │
│   └── modules/
│       ├── identity/                 # Identity & Auth Module
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   ├── value_objects/
│       │   │   ├── services/
│       │   │   ├── events/
│       │   │   └── exceptions/
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   ├── queries/
│       │   │   ├── services/
│       │   │   └── interfaces/
│       │   ├── infrastructure/
│       │   │   ├── persistence/
│       │   │   └── adapters/
│       │   ├── api/
│       │   │   ├── views/
│       │   │   ├── serializers/
│       │   │   └── urls.py
│       │   └── README.md
│       │
│       ├── hr/                       # HR Core Module
│       │   ├── domain/
│       │   ├── application/
│       │   ├── infrastructure/
│       │   ├── api/
│       │   └── README.md
│       │
│       ├── attendance/               # Attendance Module
│       │   └── ...
│       │
│       ├── leave/                    # Leave Module
│       │   └── ...
│       │
│       ├── recruitment/              # Recruitment Module
│       │   └── ...
│       │
│       ├── payroll/                  # Payroll Module
│       │   └── ...
│       │
│       ├── accounts/                 # Accounting Module
│       │   └── ...
│       │
│       └── procurement/              # Procurement Module
│           └── ...
│
├── tests/
│   ├── unit/
│   │   ├── shared/
│   │   └── modules/
│   │       ├── identity/
│   │       ├── hr/
│   │       └── ...
│   ├── integration/
│   │   └── modules/
│   └── e2e/
│
├── manage.py
└── erp_root/
    ├── settings.py
    └── urls.py
```

---

## Module Designs

### Module Dependency Map

```
                    ┌──────────────┐
                    │   Identity   │
                    │ (Users/Auth) │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────────┐
        │   HR    │  │ Accounts│  │ Procurement │
        └────┬────┘  └────┬────┘  └─────────────┘
             │            │
     ┌───────┼───────┐    │
     │       │       │    │
     ▼       ▼       ▼    │
┌────────┐ ┌─────┐ ┌──────┴───┐
│Recruit-│ │Leave│ │ Payroll  │
│  ment  │ │     │ │          │
└────────┘ └─────┘ └──────────┘

┌────────────┐
│ Attendance │ (depends on HR only)
└────────────┘
```

---

### Module 1: Shared Kernel

**Purpose:** Common building blocks used by all modules.

#### Value Objects

| Object | Fields | Purpose |
|--------|--------|---------|
| `Money` | amount, currency | Financial amounts with currency |
| `DateRange` | start_date, end_date | Date periods with validation |
| `Period` | year, month | Payroll/reporting periods |
| `Email` | value | Validated email address |
| `PhoneNumber` | value, country_code | Validated phone |
| `NationalId` | value | Zimbabwe national ID |
| `EmployeeId` | value | EMP0001 format |

#### Base Classes

| Class | Purpose |
|-------|---------|
| `Entity` | Base with ID and equality |
| `AggregateRoot` | Entity that owns consistency boundary |
| `ValueObject` | Immutable, equality by value |
| `DomainEvent` | Base for all events |
| `DomainException` | Business rule violations |

#### Infrastructure

| Component | Purpose |
|-----------|---------|
| `EventBus` | Publish/subscribe for domain events |
| `UnitOfWork` | Transaction management |
| `IRepository` | Base repository interface |

---

### Module 2: Identity

**Purpose:** User management, authentication, authorization.

#### Domain

**Entities:**
- `User` (aggregate root)
  - id, email, hashed_password
  - first_name, last_name
  - is_active, is_staff
  - failed_attempts, lockout_until
- `Role`
  - id, name, display_name
  - permissions (list)
- `AuditLogEntry`
  - user_id, event_type, ip_address
  - timestamp, details

**Value Objects:**
- `HashedPassword`
- `RoleName`
- `Permission`

**Domain Services:**
- `PasswordHasher` - Hash and verify passwords
- `LockoutPolicy` - Handle failed attempts

**Events:**
- `UserCreated`
- `UserLocked`
- `UserUnlocked`
- `LoginSucceeded`
- `LoginFailed`

#### Interfaces Exposed

```python
class IIdentityService(Protocol):
    def authenticate(self, email: str, password: str) -> AuthResult: ...
    def get_user(self, user_id: UUID) -> UserDTO: ...
    def check_permission(self, user_id: UUID, permission: str) -> bool: ...

class ICurrentUserProvider(Protocol):
    def get_current_user(self) -> UserDTO: ...
    def get_current_permissions(self) -> list[str]: ...
```

---

### Module 3: HR Core

**Purpose:** Employee and organizational management.

#### Domain

**Aggregates:**

`Employee` (root):
- id, employee_id (EMP0001)
- personal: first_name, surname, national_id, dob, gender, marital_status
- contact: email, phone
- employment: department_id, position_id, role_id, employee_type, date_joined
- contract: contract_from, contract_to, is_active
- compensation: usd_salary, zig_salary, pay_frequency
- banking: bank_name, bank_account
- statutory: nssa_number, paye_number, zimra_number
- emergency: contact_name, contact_phone, contact_relationship

`Department` (root):
- id, name, description

`Position` (root):
- id, title, department_id, description

**Value Objects:**
- `EmploymentType` (FullTime, PartTime, Contract, Intern)
- `Salary` (usd_amount, zig_amount)
- `BankAccount` (bank_name, account_number)

**Domain Services:**
- `EmployeeIdGenerator` - Generate next EMP number
- `EmployeeValidator` - Business rule validation

**Events:**
- `EmployeeHired`
- `EmployeeTerminated`
- `EmployeeUpdated`
- `SalaryChanged`
- `DepartmentChanged`

#### Interfaces Exposed

```python
class IEmployeeProvider(Protocol):
    def get_employee(self, id: int) -> EmployeeDTO: ...
    def get_employee_by_employee_id(self, employee_id: str) -> EmployeeDTO: ...
    def get_active_employees(self) -> list[EmployeeDTO]: ...
    def get_employees_by_department(self, dept_id: int) -> list[EmployeeDTO]: ...
    def get_employee_salary(self, id: int) -> SalaryDTO: ...

class IDepartmentProvider(Protocol):
    def get_department(self, id: int) -> DepartmentDTO: ...
    def get_all_departments(self) -> list[DepartmentDTO]: ...
```

---

### Module 4: Attendance

**Purpose:** Time tracking and QR-based clock in/out.

#### Domain

**Aggregates:**

`AttendanceRecord` (root):
- id, employee_id, date
- time_in, time_out
- status (calculated)

`QRToken` (root):
- id, token (32 chars)
- created_at, expires_at
- is_active, used_count

**Value Objects:**
- `ClockTime` (time value)
- `AttendanceStatus` (Present, Absent, Late, HalfDay)
- `WorkDuration` (hours, minutes)

**Domain Services:**
- `QRTokenGenerator` - Generate secure tokens
- `QRTokenValidator` - Validate and expire tokens
- `AttendanceSummaryCalculator` - Monthly summaries
- `LateArrivalDetector` - Check against schedule

**Events:**
- `EmployeeClockedIn`
- `EmployeeClockedOut`
- `QRTokenGenerated`
- `QRTokenUsed`

#### Dependencies

- HR Module (IEmployeeProvider)

---

### Module 5: Leave

**Purpose:** Leave management and approval workflow.

#### Domain

**Aggregates:**

`LeaveType` (root):
- id, name
- default_days_allowed
- is_active

`LeaveBalance` (root):
- id, employee_id, leave_type_id
- year
- entitled_days, used_days, remaining_days

`LeaveRequest` (root):
- id, employee_id, leave_type_id
- start_date, end_date, days_count
- reason
- status (Pending, Approved, Rejected, Cancelled)
- requested_at, reviewed_by, reviewed_at

**Value Objects:**
- `LeaveStatus`
- `LeavePeriod` (start, end, days)

**Domain Services:**
- `LeaveBalanceCalculator` - Calculate remaining days
- `LeaveConflictDetector` - Check overlapping leaves
- `LeaveApprovalPolicy` - Approval rules

**Events:**
- `LeaveRequested`
- `LeaveApproved`
- `LeaveRejected`
- `LeaveCancelled`
- `LeaveBalanceAdjusted`

#### Interfaces Exposed

```python
class ILeaveProvider(Protocol):
    def get_leave_balance(self, employee_id: int, year: int) -> list[LeaveBalanceDTO]: ...
    def get_leave_days_in_period(self, employee_id: int, start: date, end: date) -> int: ...
    def get_approved_leaves(self, employee_id: int, period: Period) -> list[LeaveDTO]: ...
```

#### Dependencies

- HR Module (IEmployeeProvider)
- Identity Module (ICurrentUserProvider for approver)

---

### Module 6: Recruitment

**Purpose:** Job postings and hiring pipeline.

#### Domain

**Aggregates:**

`Job` (root):
- id, title
- department_id, position_id
- status (Draft, Open, Closed)
- location, reports_to
- salary_usd_min/max, salary_zig_min/max
- description, responsibilities, qualifications, competencies
- application_process, contact_email
- is_internal, posted_date

`Candidate` (root):
- id, national_id
- first_name, last_name
- email, phone, address
- date_of_birth
- qualifications, experience
- resume_path

`Application` (root):
- id, job_id, candidate_id
- cover_letter
- status (Pending, Shortlisted, Interview, Offered, Hired, Rejected)
- applied_at, updated_at

**Value Objects:**
- `JobStatus`
- `ApplicationStatus`
- `SalaryRange`

**Domain Services:**
- `ApplicationProcessor` - Status transitions
- `HiringService` - Convert candidate to employee

**Events:**
- `JobPosted`
- `JobClosed`
- `ApplicationReceived`
- `ApplicationStatusChanged`
- `CandidateHired`

#### Dependencies

- HR Module (IEmployeeProvider for creating employee on hire)

---

### Module 7: Payroll

**Purpose:** Salary processing, tax calculation, payslips.

#### Domain

**Aggregates:**

`TaxTable` (root):
- id, currency
- brackets (list of TaxBracket)
- effective_from

`Payroll` (root):
- id, period (year, month)
- status (Open, Processing, Closed)
- processed_at, processed_by

`Payslip` (root):
- id, payroll_id, employee_id
- period
- base_salary_usd/zig
- allowances_usd/zig
- gross_usd/zig
- paye_usd/zig
- aids_levy_usd/zig
- nssa_employee_usd/zig
- nssa_employer_usd/zig
- other_deductions_usd/zig
- total_deductions_usd/zig
- net_salary_usd/zig
- exchange_rate
- status (Draft, Processed, Paid)

`ExchangeRate` (root):
- id, date
- zig_to_usd_rate

`AllowanceType` / `DeductionType`:
- id, name, description
- default_amount, currency

`EmployeeAllowance` / `EmployeeDeduction`:
- id, employee_id, type_id
- amount, currency

**Value Objects:**
- `TaxBracket` (min, max, rate, deduction)
- `PayrollPeriod` (year, month)
- `PayslipStatus`
- `Earnings` (breakdown)
- `Deductions` (breakdown)

**Domain Services:**
- `TaxCalculator` - PAYE calculation using brackets
- `NSSACalculator` - 4.5% employee, 4.5% employer
- `AIDSLevyCalculator` - 3% of PAYE
- `AllowanceCalculator` - Sum employee allowances
- `DeductionCalculator` - Sum employee deductions
- `GrossPayCalculator` - Base + allowances
- `NetPayCalculator` - Gross - all deductions
- `PayslipGenerator` - Orchestrate full calculation

**Events:**
- `PayrollOpened`
- `PayrollProcessed`
- `PayrollClosed`
- `PayslipGenerated`
- `PayslipPaid`

#### Interfaces Exposed

```python
class IPayrollProvider(Protocol):
    def get_payslip(self, employee_id: int, period: Period) -> PayslipDTO: ...
    def get_payroll_summary(self, period: Period) -> PayrollSummaryDTO: ...
```

#### Dependencies

- HR Module (IEmployeeProvider for salary, employee data)
- Leave Module (ILeaveProvider for leave days)
- Accounts Module (via events for journal entries)

---

### Module 8: Accounts

**Purpose:** Financial accounting and reporting.

#### Domain

**Aggregates:**

`Account` (root):
- id, code, name
- parent_id (hierarchical)
- account_type (Asset, Liability, Equity, Revenue, Expense)
- currency_id
- is_reconcilable

`Journal` (root):
- id, code, name
- journal_type (Sales, Purchase, Cash, Bank, General)
- default_debit_account_id
- default_credit_account_id

`JournalEntry` (root):
- id, journal_id
- date, reference, narration
- is_posted
- lines (list of JournalEntryLine)

`JournalEntryLine`:
- id, entry_id, account_id
- partner_id (optional)
- debit, credit
- currency_id, amount_currency

`Partner` (root):
- id, name
- partner_type (Customer, Supplier, Employee)
- vat_number

`Currency` (root):
- id, code, name, symbol
- rate_to_base

**Value Objects:**
- `AccountCode`
- `AccountType`
- `JournalType`
- `DebitCredit`

**Domain Services:**
- `BalanceCalculator` - Account balances
- `TrialBalanceGenerator`
- `ProfitLossGenerator`
- `BalanceSheetGenerator`

**Events:**
- `JournalEntryPosted`
- `AccountCreated`

#### Event Handlers

Listens to:
- `PayrollProcessed` → Create salary expense journal entries

---

### Module 9: Procurement

**Purpose:** Purchase requests, orders, suppliers.

#### Domain

**Aggregates:**

`Supplier` (root):
- id, name
- contact_person, email, phone
- address
- is_active

`BudgetCenter` (root):
- id, name, code
- allocated_amount, spent_amount
- year

`PurchaseRequest` (root):
- id, requester_id
- budget_center_id
- description, justification
- estimated_amount, currency
- status (Draft, Submitted, Approved, Rejected)
- requested_at, approved_by, approved_at

`PurchaseOrder` (root):
- id, request_id, supplier_id
- order_number
- items (list)
- total_amount
- status (Draft, Sent, Received, Cancelled)
- ordered_at, received_at

**Value Objects:**
- `RequestStatus`
- `OrderStatus`
- `OrderItem`

**Domain Services:**
- `BudgetChecker` - Verify budget availability
- `ApprovalWorkflow` - Multi-level approval

**Events:**
- `PurchaseRequested`
- `PurchaseApproved`
- `PurchaseRejected`
- `OrderPlaced`
- `GoodsReceived`

---

## Implementation Phases

### Phase 0: Foundation Setup

**Duration:** 1 week

| Task | Description | Output |
|------|-------------|--------|
| 0.1 | Create new directory structure | `src/`, `tests/` folders |
| 0.2 | Configure Python path and imports | Updated settings |
| 0.3 | Set up test infrastructure | pytest, factories |
| 0.4 | Create code quality tooling | linting, formatting |
| 0.5 | Document architecture decisions | ADR documents |

**Delete:** Nothing yet

---

### Phase 1: Shared Kernel

**Duration:** 1 week

| Task | Description | Files |
|------|-------------|-------|
| 1.1 | Implement Money value object | `shared/domain/value_objects/money.py` |
| 1.2 | Implement DateRange value object | `shared/domain/value_objects/date_range.py` |
| 1.3 | Implement Period value object | `shared/domain/value_objects/period.py` |
| 1.4 | Implement other value objects | Email, Phone, NationalId, EmployeeId |
| 1.5 | Implement base classes | Entity, AggregateRoot, ValueObject |
| 1.6 | Implement DomainEvent base | `shared/domain/base/domain_event.py` |
| 1.7 | Implement exceptions | `shared/domain/exceptions/` |
| 1.8 | Implement EventBus | `shared/infrastructure/event_bus.py` |
| 1.9 | Implement UnitOfWork | `shared/infrastructure/unit_of_work.py` |
| 1.10 | Write comprehensive tests | `tests/unit/shared/` |

**Delete:** Nothing yet

---

### Phase 2: Identity Module

**Duration:** 1-2 weeks

| Task | Description |
|------|-------------|
| 2.1 | Create module structure | `src/modules/identity/` |
| 2.2 | Implement User entity | Domain layer |
| 2.3 | Implement Role entity | Domain layer |
| 2.4 | Implement AuditLogEntry | Domain layer |
| 2.5 | Implement domain services | PasswordHasher, LockoutPolicy |
| 2.6 | Implement application services | AuthService, UserService |
| 2.7 | Implement repositories | UserRepository, RoleRepository |
| 2.8 | Implement API layer | Auth views, user views |
| 2.9 | Write tests | Full coverage |
| 2.10 | Migrate `/api/auth/token/` | Delete old auth_view.py |
| 2.11 | Migrate `/api/auth/users/` | Delete old user_views.py |
| 2.12 | Migrate `/api/auth/logs/` | Delete old audit_view.py |
| 2.13 | Delete legacy auth app | Remove `authentication/` folder |

**Delete:** `authentication/` app completely

---

### Phase 3: HR Core Module

**Duration:** 2-3 weeks

| Task | Description |
|------|-------------|
| 3.1 | Create module structure | `src/modules/hr/` |
| 3.2 | Implement Employee aggregate | All business rules |
| 3.3 | Implement Department aggregate | |
| 3.4 | Implement Position aggregate | |
| 3.5 | Implement domain services | EmployeeIdGenerator |
| 3.6 | Implement application services | EmployeeAppService |
| 3.7 | Implement repositories | |
| 3.8 | Implement IEmployeeProvider | Interface for other modules |
| 3.9 | Implement API layer | |
| 3.10 | Write tests | |
| 3.11 | Migrate employee endpoints | Delete old views one by one |
| 3.12 | Migrate department endpoints | |
| 3.13 | Migrate position endpoints | |
| 3.14 | Delete legacy HR models | Keep only what's needed for unmigrated modules |

**Delete:** Employee, Department, Position from `human_resources/`

---

### Phase 4: Attendance Module

**Duration:** 1-2 weeks

| Task | Description |
|------|-------------|
| 4.1 | Create module structure | `src/modules/attendance/` |
| 4.2 | Implement AttendanceRecord aggregate | |
| 4.3 | Implement QRToken aggregate | |
| 4.4 | Implement domain services | QRTokenGenerator, etc. |
| 4.5 | Implement application services | |
| 4.6 | Implement repositories | |
| 4.7 | Implement API layer | Including QR endpoints |
| 4.8 | Write tests | |
| 4.9 | Migrate attendance endpoints | |
| 4.10 | Delete legacy attendance code | |

**Delete:** AttendanceRecord, QRToken from old locations

---

### Phase 5: Leave Module

**Duration:** 2 weeks

| Task | Description |
|------|-------------|
| 5.1 | Create module structure | `src/modules/leave/` |
| 5.2 | Implement LeaveType aggregate | |
| 5.3 | Implement LeaveBalance aggregate | |
| 5.4 | Implement LeaveRequest aggregate | |
| 5.5 | Implement domain services | |
| 5.6 | Implement ILeaveProvider | |
| 5.7 | Implement application services | |
| 5.8 | Implement repositories | |
| 5.9 | Implement API layer | |
| 5.10 | Write tests | |
| 5.11 | Migrate leave endpoints | |
| 5.12 | Delete legacy leave code | |

**Delete:** Leave models from `human_resources/`

---

### Phase 6: Recruitment Module

**Duration:** 2 weeks

| Task | Description |
|------|-------------|
| 6.1 | Create module structure | `src/modules/recruitment/` |
| 6.2 | Implement Job aggregate | |
| 6.3 | Implement Candidate aggregate | |
| 6.4 | Implement Application aggregate | |
| 6.5 | Implement HiringService | Creates employee via HR module |
| 6.6 | Implement application services | |
| 6.7 | Implement repositories | |
| 6.8 | Implement API layer | Public and admin |
| 6.9 | Write tests | |
| 6.10 | Migrate job endpoints | |
| 6.11 | Migrate application endpoints | |
| 6.12 | Migrate public career endpoints | |
| 6.13 | Delete legacy recruitment code | |

**Delete:** Job, Candidate, JobApplication from `human_resources/`

---

### Phase 7: Payroll Module

**Duration:** 3-4 weeks

| Task | Description |
|------|-------------|
| 7.1 | Create module structure | `src/modules/payroll/` |
| 7.2 | Implement TaxTable aggregate | With TaxBracket |
| 7.3 | Implement ExchangeRate aggregate | |
| 7.4 | Implement AllowanceType/DeductionType | |
| 7.5 | Implement Payslip aggregate | |
| 7.6 | Implement Payroll aggregate | |
| 7.7 | Implement TaxCalculator | PAYE logic |
| 7.8 | Implement NSSACalculator | |
| 7.9 | Implement AIDSLevyCalculator | |
| 7.10 | Implement PayslipGenerator | Orchestration |
| 7.11 | Implement IPayrollProvider | |
| 7.12 | Implement application services | |
| 7.13 | Implement repositories | |
| 7.14 | Implement API layer | |
| 7.15 | Implement event publishing | PayrollProcessed |
| 7.16 | Write extensive tests | Tax calculations critical |
| 7.17 | Migrate payroll endpoints | |
| 7.18 | Migrate payslip endpoints | |
| 7.19 | Migrate rate endpoints | |
| 7.20 | Delete legacy payroll code | |

**Delete:** Entire `payroll/` app

---

### Phase 8: Accounts Module

**Duration:** 2-3 weeks

| Task | Description |
|------|-------------|
| 8.1 | Create module structure | `src/modules/accounts/` |
| 8.2 | Implement Account aggregate | Hierarchical |
| 8.3 | Implement Journal aggregate | |
| 8.4 | Implement JournalEntry aggregate | |
| 8.5 | Implement Partner aggregate | |
| 8.6 | Implement Currency aggregate | |
| 8.7 | Implement reporting services | |
| 8.8 | Implement event handlers | Listen to PayrollProcessed |
| 8.9 | Implement application services | |
| 8.10 | Implement repositories | |
| 8.11 | Implement API layer | |
| 8.12 | Write tests | |
| 8.13 | Migrate accounts endpoints | |
| 8.14 | Delete legacy accounts code | |

**Delete:** Entire `accounts/` app

---

### Phase 9: Procurement Module

**Duration:** 2 weeks

| Task | Description |
|------|-------------|
| 9.1 | Create module structure | `src/modules/procurement/` |
| 9.2 | Implement Supplier aggregate | |
| 9.3 | Implement BudgetCenter aggregate | |
| 9.4 | Implement PurchaseRequest aggregate | |
| 9.5 | Implement PurchaseOrder aggregate | |
| 9.6 | Implement domain services | BudgetChecker, ApprovalWorkflow |
| 9.7 | Implement application services | |
| 9.8 | Implement repositories | |
| 9.9 | Implement API layer | |
| 9.10 | Write tests | |
| 9.11 | Migrate procurement endpoints | |
| 9.12 | Delete legacy procurement code | |

**Delete:** Entire `procurement/` app

---

### Phase 10: Portal API Consolidation

**Duration:** 1-2 weeks

| Task | Description |
|------|-------------|
| 10.1 | Create portal API structure | Dedicated endpoints |
| 10.2 | Implement portal auth | EC number login |
| 10.3 | Implement portal dashboard | Aggregated data |
| 10.4 | Implement portal attendance | Uses Attendance module |
| 10.5 | Implement portal leave | Uses Leave module |
| 10.6 | Implement portal payslips | Uses Payroll module |
| 10.7 | Implement public careers | Uses Recruitment module |
| 10.8 | Write tests | |
| 10.9 | Delete legacy employee_portal | |

**Delete:** Entire `employee_portal/` app

---

### Phase 11: Final Cleanup

**Duration:** 1 week

| Task | Description |
|------|-------------|
| 11.1 | Remove all legacy folders | Verify nothing remains |
| 11.2 | Update URL configuration | Clean routing |
| 11.3 | Update settings | Remove old apps |
| 11.4 | Run full test suite | Ensure nothing broken |
| 11.5 | Performance testing | Identify issues |
| 11.6 | Security review | Auth, permissions |
| 11.7 | Update documentation | Final architecture docs |
| 11.8 | Generate API documentation | OpenAPI spec |

**Delete:** Any remaining legacy code, `administration/` app if empty

---

## Timeline Summary

| Phase | Name | Duration | Cumulative |
|-------|------|----------|------------|
| 0 | Foundation Setup | 1 week | 1 week |
| 1 | Shared Kernel | 1 week | 2 weeks |
| 2 | Identity Module | 1-2 weeks | 4 weeks |
| 3 | HR Core Module | 2-3 weeks | 7 weeks |
| 4 | Attendance Module | 1-2 weeks | 9 weeks |
| 5 | Leave Module | 2 weeks | 11 weeks |
| 6 | Recruitment Module | 2 weeks | 13 weeks |
| 7 | Payroll Module | 3-4 weeks | 17 weeks |
| 8 | Accounts Module | 2-3 weeks | 20 weeks |
| 9 | Procurement Module | 2 weeks | 22 weeks |
| 10 | Portal API | 1-2 weeks | 24 weeks |
| 11 | Final Cleanup | 1 week | 25 weeks |

**Total: Approximately 6 months**

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Breaking production | Migrate one endpoint at a time, test thoroughly before deleting old code |
| Data loss | Same database, just new code accessing it |
| Incomplete migration | Track every endpoint, don't delete until replacement works |
| Knowledge gaps | Document everything, create examples |
| Scope creep | No new features during refactoring |
| Test gaps | Write tests before migrating each piece |
| Team confusion | Regular reviews, clear documentation |

---

## Success Criteria

### Per Phase

- [ ] All tests pass
- [ ] All endpoints migrated and working
- [ ] Legacy code for that module deleted
- [ ] Documentation updated
- [ ] No regressions

### Overall Project

- [ ] Zero legacy code remaining
- [ ] 90%+ test coverage
- [ ] All modules follow clean architecture
- [ ] No file exceeds 400 lines
- [ ] Documentation complete
- [ ] API documentation generated

---

## Appendix: File Templates

### Domain Entity Template

```
src/modules/{module}/domain/entities/{entity}.py

- Imports (max 10 lines)
- Class docstring
- Class definition
- Properties (grouped logically)
- Business methods
- Validation methods
- Factory methods (if needed)

Total: < 200 lines ideal, < 400 max
```

### Application Service Template

```
src/modules/{module}/application/services/{service}.py

- Imports
- Class docstring
- Constructor with dependencies
- Public methods (use cases)
- Private helper methods

Total: < 200 lines ideal, < 400 max
```

### Repository Template

```
src/modules/{module}/infrastructure/persistence/{repository}.py

- Imports
- Class docstring
- Constructor
- CRUD methods
- Query methods
- Mapping methods (entity <-> model)

Total: < 200 lines ideal, < 400 max
```

---

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin Phase 0: Foundation Setup
4. Weekly progress reviews

---

*Document maintained by: Development Team*
*Last updated: March 2026*

# ZCHPC ERP System Architecture

## Overview

The ZCHPC ERP system follows a **Modular Monolith** architecture with **Clean Architecture** principles.
 This document describes the current system structure and provides guidance for development.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  /api/v2/*  (New Modular Architecture - Recommended)                ││
│  │  /api/*     (Legacy Endpoints - Deprecated)                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                         Application Layer                                │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Services, Commands, Queries, DTOs                                  ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                           Domain Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Entities, Value Objects, Domain Services, Events                   ││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                       Infrastructure Layer                               │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Django Models, Repositories, External Services                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

### Directory Layout

```
erp_project/
├── src/
│   ├── shared/                    # Shared Kernel
│   │   ├── domain/
│   │   │   ├── base/              # Entity, AggregateRoot, ValueObject
│   │   │   ├── value_objects/     # Money, DateRange, Period
│   │   │   └── exceptions/        # Domain exceptions
│   │   └── infrastructure/
│   │       └── event_bus.py       # Domain event publishing
│   │
│   └── modules/
│       ├── identity/              # Authentication & Authorization
│       ├── hr/                    # Human Resources Core
│       ├── attendance/            # Time Tracking
│       ├── leave/                 # Leave Management
│       ├── recruitment/           # Job Postings & Hiring
│       ├── payroll/               # Salary Processing
│       ├── accounts/              # Financial Accounting
│       ├── procurement/           # Purchase Management
│       └── portal/                # Employee Self-Service
│
├── authentication/                # Django models: CustomUser, AuditLog
├── human_resources/               # Django models: Employee, Department, etc.
├── payroll/                       # Django models: Payroll, TaxBracket
├── accounts/                      # Django models: Account, Journal
├── procurement/                   # Django models: Vendor, PurchaseOrder
├── employee_portal/               # Django models: ExpenseClaim, Document
├── administration/                # Placeholder (minimal)
│
└── erp_root/                      # Django project settings
    ├── settings.py
    └── urls.py
```

> **Note:** The apps at root level (authentication, human_resources, etc.) contain
> **only Django models and migrations**. All views, serializers, and URL configs
> have been moved to `src/modules/`. These apps exist solely for database schema.

### Module Internal Structure

Each module follows this internal structure:

```
modules/{module_name}/
├── domain/
│   ├── entities/           # Aggregate roots and entities
│   ├── value_objects/      # Immutable value objects
│   ├── services/           # Domain services
│   ├── events/             # Domain events
│   └── exceptions/         # Domain-specific exceptions
│
├── application/
│   ├── services/           # Application services (use cases)
│   ├── commands/           # Command handlers
│   ├── queries/            # Query handlers
│   ├── interfaces/         # Repository/Provider interfaces
│   └── dtos/               # Data transfer objects
│
├── infrastructure/
│   └── persistence/        # Django repository implementations
│
├── api/
│   ├── views.py            # API views
│   ├── serializers.py      # DRF serializers
│   └── urls.py             # URL patterns
│
├── tests/                  # Module tests
│   ├── test_entities.py
│   ├── test_value_objects.py
│   └── test_services.py
│
└── __init__.py
```

## API Structure

All API endpoints are available at `/api/v2/*`. The legacy v1 API has been removed.

### API Endpoints

| Module | Base URL | Description |
|--------|----------|-------------|
| Identity | `/api/v2/auth/` | Authentication, users |
| HR | `/api/v2/hr/` | Employees, departments, positions |
| Attendance | `/api/v2/attendance/` | Clock in/out, QR tokens |
| Leave | `/api/v2/leave/` | Leave requests, balances |
| Recruitment | `/api/v2/recruitment/` | Jobs, candidates, applications |
| Payroll | `/api/v2/payroll/` | Payslips, processing |
| Accounts | `/api/v2/accounts/` | Chart of accounts, journals |
| Procurement | `/api/v2/procurement/` | Purchase requests, orders |
| Portal | `/api/v2/portal/` | Employee self-service |

## Module Dependencies

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

┌────────────┐      ┌──────────┐
│ Attendance │      │  Portal  │
│(HR only)   │      │(All mods)│
└────────────┘      └──────────┘
```

### Dependency Rules

1. **Domain layer** has ZERO external dependencies
2. **Application layer** depends only on domain layer
3. **Infrastructure layer** implements interfaces from application layer
4. **API layer** depends on application layer
5. **Cross-module communication** uses provider interfaces

## Key Design Patterns

### 1. Repository Pattern

```python
# Interface in application layer
class IEmployeeRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Employee]: ...
    @abstractmethod
    def save(self, employee: Employee) -> Employee: ...

# Implementation in infrastructure layer
class DjangoEmployeeRepository(IEmployeeRepository):
    def get_by_id(self, id: int) -> Optional[Employee]:
        # Uses Django ORM, maps to domain entity
        ...
```

### 2. Provider Pattern (Cross-Module)

```python
# Interface for cross-module communication
class IEmployeeProvider(ABC):
    @abstractmethod
    def get_employee(self, id: int) -> EmployeeDTO: ...

# Used by Payroll module to get employee data from HR module
class PayrollService:
    def __init__(self, employee_provider: IEmployeeProvider):
        self.employee_provider = employee_provider
```

### 3. Value Objects

```python
@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise CurrencyMismatchError()
        return Money(self.amount + other.amount, self.currency)
```

### 4. Aggregate Roots

```python
@dataclass
class Employee(AggregateRoot[int]):
    employee_id: str
    first_name: str
    surname: str
    department_id: int
    salary: Money

    def change_department(self, new_department_id: int) -> None:
        self.department_id = new_department_id
        self.add_event(DepartmentChanged(self.id, new_department_id))
```

## Code Standards

### File Size Limit

**Maximum 400 lines per file.** No exceptions.

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module folder | lowercase, singular | `payroll/` |
| Python file | lowercase, underscore | `tax_calculator.py` |
| Class | PascalCase | `TaxCalculator` |
| Function | lowercase, underscore | `calculate_paye()` |
| Interface | I + Name | `IEmployeeRepository` |

### Testing Requirements

| Layer | Test Type | Target |
|-------|-----------|--------|
| Domain | Unit tests | 95%+ |
| Application | Integration | 90%+ |
| Infrastructure | Integration | 80%+ |
| API | Contract tests | 100% |

## Database

The system uses **PostgreSQL** with Django ORM.

### Key Models

- **authentication.CustomUser** - System users
- **human_resources.Employees** - Employee records
- **human_resources.Department** - Organizational units
- **payroll.Payroll** - Payslip records
- **accounts.AccountChart** - Chart of accounts

### Migration Strategy

Django models remain in legacy apps. New modules use:
1. Domain entities for business logic
2. Repository pattern for persistence
3. Django ORM in infrastructure layer

## Security

### Authentication

- JWT tokens via SimpleJWT
- EC number login for employee portal
- Role-based access control (RBAC)

### Authorization

Middleware handles permission checks:
- `JWTAuthenticationMiddleware` - Token validation
- `RBACMiddleware` - Role-based permissions

## Development Guidelines

### Adding New Features

1. Create domain entities and value objects
2. Define repository interfaces
3. Implement application services
4. Create API endpoints
5. Write tests at each layer

### Modifying Existing Features

1. Check if it's in legacy or new module
2. For legacy: Consider migrating to new module first
3. For new module: Follow clean architecture layers

### Running Tests

```bash
# Run all tests
pytest

# Run specific module tests
pytest src/modules/hr/tests/

# Run with coverage
pytest --cov=src/modules
```

## References

- [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) - Detailed migration plan
- [API_REFERENCE.md](./API_REFERENCE.md) - API documentation
- [adr/](../erp_project/docs/adr/) - Architecture Decision Records

---

*Last updated: March 2026*

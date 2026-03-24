# Source Code Directory

This directory contains the refactored modular monolith architecture.

## Structure

```
src/
├── shared/           # Shared Kernel - common building blocks
│   ├── domain/       # Value objects, base classes, exceptions
│   └── infrastructure/  # Event bus, unit of work, base repository
│
└── modules/          # Business modules
    ├── identity/     # User management, authentication, authorization
    ├── hr/           # Employee and organizational management
    ├── attendance/   # Time tracking and QR clock in/out
    ├── leave/        # Leave management and approvals
    ├── recruitment/  # Job postings and hiring pipeline
    ├── payroll/      # Salary processing, tax, payslips
    ├── accounts/     # Financial accounting
    └── procurement/  # Purchase requests and orders
```

## Module Structure

Each module follows clean architecture:

```
module/
├── domain/           # Business logic (no external dependencies)
│   ├── entities/     # Aggregate roots and entities
│   ├── value_objects/  # Immutable value types
│   ├── services/     # Domain services
│   ├── events/       # Domain events
│   └── exceptions/   # Business rule violations
│
├── application/      # Use cases
│   ├── commands/     # Write operations
│   ├── queries/      # Read operations
│   ├── services/     # Application services
│   └── interfaces/   # Contracts for other modules
│
├── infrastructure/   # External concerns
│   ├── persistence/  # Repositories, Django models
│   └── adapters/     # External service adapters
│
├── api/              # HTTP layer
│   ├── views/        # DRF views
│   ├── serializers/  # Request/response serializers
│   └── urls.py       # URL routing
│
└── README.md         # Module documentation
```

## Dependency Rules

1. **Domain** has zero external dependencies
2. **Application** depends only on Domain
3. **Infrastructure** depends on Domain and Application
4. **API** depends on Application (not directly on Domain)

Dependencies always point inward toward the domain.

## Code Standards

- Maximum 400 lines per file
- One class per file (preferred)
- Comprehensive docstrings on public classes/methods
- 90%+ test coverage target

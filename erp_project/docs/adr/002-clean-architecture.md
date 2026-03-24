# ADR-002: Use Clean Architecture Layers

## Status

Accepted

## Context

Within each module, we need a consistent structure that:

- Separates business logic from infrastructure
- Makes the domain testable without Django/database
- Allows swapping infrastructure components
- Keeps the codebase maintainable

Options considered:

1. **Traditional Django** - models, views, serializers
2. **Hexagonal Architecture** - ports and adapters
3. **Clean Architecture** - domain, application, infrastructure, API layers

## Decision

We will use **Clean Architecture** with four layers:

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
```

### Dependency Rule

Dependencies only point inward:
- API depends on Application
- Application depends on Domain
- Infrastructure depends on Domain and Application
- **Domain has zero external dependencies**

### Layer Responsibilities

**Domain Layer:**
- Business entities and aggregates
- Value objects (immutable)
- Domain services (pure business logic)
- Domain events
- Business rule exceptions

**Application Layer:**
- Use cases (commands and queries)
- Application services that orchestrate
- Interfaces/contracts for other modules
- DTOs for data transfer

**Infrastructure Layer:**
- Repository implementations
- Django models (ORM)
- External service adapters
- Database queries

**API Layer:**
- REST views
- Request/response serializers
- URL routing
- Authentication/authorization

## Consequences

### Positive

- Domain logic is pure Python, no Django dependencies
- Easy to unit test domain without database
- Infrastructure can be swapped (e.g., different database)
- Clear separation of concerns
- Business rules are explicit and centralized

### Negative

- More files and directories
- Mapping between layers (entity ↔ model)
- Learning curve for developers new to clean architecture
- More boilerplate initially

### Trade-offs Accepted

- We accept the additional structure for maintainability
- Mapping code is worth the isolation it provides
- New patterns will be documented with examples

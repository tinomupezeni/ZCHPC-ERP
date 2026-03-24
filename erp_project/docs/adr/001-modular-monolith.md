# ADR-001: Adopt Modular Monolith Architecture

## Status

Accepted

## Context

The current ERP backend is a traditional Django monolith with tightly coupled apps. Business logic is scattered across views, serializers, and models. This leads to:

- Difficult maintenance as the codebase grows
- Hard to understand module boundaries
- Challenging to test in isolation
- Risk of unintended side effects when making changes

We considered three options:

1. **Keep current structure** - Continue with Django apps, add conventions
2. **Microservices** - Split into separate deployable services
3. **Modular Monolith** - Single deployment with strict module boundaries

## Decision

We will refactor to a **Modular Monolith** architecture.

### Why Not Microservices?

- Team size doesn't justify operational complexity
- Network latency between services adds overhead
- Distributed transactions are complex
- We don't need independent scaling per module
- Single database is sufficient for our load

### Why Not Keep Current Structure?

- Coupling will continue to increase
- Testing becomes increasingly difficult
- New developers struggle to understand boundaries
- Business logic remains scattered

### Why Modular Monolith?

- Clear module boundaries without network overhead
- Easier to reason about than distributed systems
- Can extract to microservices later if needed
- Single deployment simplifies operations
- Modules can be tested in isolation
- Enforces discipline through structure

## Consequences

### Positive

- Clear ownership boundaries for each module
- Easier onboarding for new developers
- Each module can be understood independently
- Simpler deployment and operations
- Can evolve to microservices if needed

### Negative

- Requires discipline to maintain boundaries
- Initial refactoring effort is significant
- All modules share the same deployment
- Must be careful about module coupling

### Risks Mitigated

- Module interfaces enforce contracts
- Code review ensures boundary respect
- Tests verify module isolation

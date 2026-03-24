# ADR-005: Delete-As-You-Go Migration Strategy

## Status

Accepted

## Context

When refactoring a codebase, there are two common approaches:

1. **Parallel running** - Keep old and new code, switch gradually
2. **Delete as you go** - Remove old code immediately after migrating

Each has trade-offs:

### Parallel Running

Pros:
- Can rollback easily
- Less risk per change

Cons:
- Codebase grows larger temporarily
- Confusion about which code is authoritative
- Easy to forget to delete old code
- Tests must cover both paths

### Delete As You Go

Pros:
- Always clear what's current
- No dead code accumulation
- Forces complete migration of each piece
- Smaller codebase at any point

Cons:
- Must be confident before deleting
- Harder to rollback (use git)
- Requires thorough testing

## Decision

We will **delete old code immediately** after each endpoint/feature is migrated.

### Migration Process

For each endpoint:

1. **Build** - Implement in new module
2. **Test** - Comprehensive tests for new code
3. **Wire** - Route to new implementation
4. **Verify** - Confirm working in dev/staging
5. **Delete** - Remove old code immediately
6. **Commit** - Single commit with migration + deletion

### No Transition Period

- No adapters bridging old and new
- No feature flags for old vs new
- No parallel implementations

### Safety Measures

- Comprehensive tests before deletion
- Git history preserves old code if needed
- Small incremental migrations (one endpoint at a time)
- Review each deletion in PR

## Consequences

### Positive

- Codebase never has duplicate implementations
- Always clear what code is active
- Forces thorough testing before migration
- Simpler mental model
- No cleanup phase needed later

### Negative

- Must be more careful with each migration
- Can't easily A/B test old vs new
- Rollback requires git revert

### Risks Mitigated

- Thorough test coverage before deletion
- Small migration units reduce blast radius
- Code review catches incomplete migrations
- CI/CD catches regressions quickly

# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the ZCHPC ERP system.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [001](001-modular-monolith.md) | Adopt Modular Monolith Architecture | Accepted | 2026-03 |
| [002](002-clean-architecture.md) | Use Clean Architecture Layers | Accepted | 2026-03 |
| [003](003-domain-events.md) | Inter-Module Communication via Events | Accepted | 2026-03 |
| [004](004-file-size-limit.md) | 400-Line File Size Limit | Accepted | 2026-03 |
| [005](005-delete-as-you-go.md) | Delete-As-You-Go Migration Strategy | Accepted | 2026-03 |

## Template

New ADRs should follow this template:

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```

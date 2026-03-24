# ADR-004: 400-Line File Size Limit

## Status

Accepted

## Context

Large files are hard to:
- Understand at a glance
- Review in pull requests
- Navigate and maintain
- Test in isolation

The current codebase has files exceeding 1000 lines, mixing multiple responsibilities.

## Decision

**Maximum 400 lines per Python file. No exceptions.**

### Enforcement

1. **Pre-commit hook** - Blocks commits with files > 400 lines
2. **CI check** - Fails builds with oversized files
3. **Code review** - Reviewers reject large files

### When Approaching 400 Lines

If a file is growing large:

1. **Split by responsibility** - Extract classes to separate files
2. **Split by abstraction** - Move helpers to utils
3. **Create sub-packages** - Group related smaller files

### What Counts

- All `.py` files in `src/`
- All `.py` files in `tests/`
- Excluding `migrations/` (auto-generated)
- Excluding `__init__.py` (usually just imports)

### Practical Guidelines

| File Type | Target Lines | Max Lines |
|-----------|--------------|-----------|
| Entity | 100-150 | 400 |
| Service | 100-200 | 400 |
| Repository | 100-200 | 400 |
| View | 50-100 | 400 |
| Serializer | 50-100 | 400 |
| Test file | 100-300 | 400 |

## Consequences

### Positive

- Files are easy to understand
- Single responsibility is enforced
- Code reviews are manageable
- Navigation is straightforward
- Encourages proper decomposition

### Negative

- More files to manage
- More imports between files
- May feel restrictive initially

### Trade-offs Accepted

- More files is better than large files
- Import management is IDE-assisted
- Discipline leads to better design

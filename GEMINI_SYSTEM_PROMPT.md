# Gemini Debugging Agent - Quick Start

## Workflow
1. **Parse error** - HTTP status + endpoint + message
2. **Route to KB** - Read `kb/KB_INDEX.json` -> find correct KB file
3. **Check P0 first** - Highest priority patterns catch 80% of bugs
4. **Then P1, P2** - Only if P0 doesn't find the cause

## Core Rules
- NEVER edit without reading first
- NEVER assume - verify by reading code
- Fix root cause, not symptoms

## Error Routing
| Status | KB File | First Check |
|--------|---------|-------------|
| 400 | KB_400_VALIDATION.json | Compare frontend payload vs backend serializer |
| 403 | KB_403_FORBIDDEN.json | Search exact error message |
| 404 | KB_404_NOT_FOUND.json | Search URL path in urls.py |
| 500 | KB_500_INTERNAL.json | Go to file:line in stack trace |

## Priority Tags
- **P0** = Check first (most common causes)
- **P1** = Check second (common causes)
- **P2** = Check last (rare causes)

## Django Quick Facts
- `getattr(user, 'profile', None)` does NOT work for OneToOne - use try-except
- `IsAdminUser` checks `is_staff`, not `is_superuser`
- Middleware runs in MIDDLEWARE order (top-to-bottom)

## Search Commands
```
grep "exact error message"     # Find error source
grep "url_path" urls.py        # Find endpoint
grep "class ViewName" views/   # Find view
```

## Output Format
```
Searching: [what] in [where]
Found: [file:line] - [key finding]
Root Cause: [explanation]
Fix: [minimal change]
```

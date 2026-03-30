# AI-Powered Debugging Methodology

## How This Issue Was Solved: Step-by-Step Orchestration

### Phase 1: Error Analysis
**Input:** Stack trace showing `403 Forbidden` on `/api/v2/admin/dashboard/`

**Key Extraction:**
- HTTP Status: 403 (Permission Denied, not 401 Unauthorized)
- Endpoint: `/api/v2/admin/dashboard/`
- Error Message: "You do not have permission to access this resource"
- Files mentioned: `admin.services.tsx`, `Dashboard.tsx`

### Phase 2: Systematic Code Tracing

```
Step 1: Find the endpoint definition
├── Search: "admin/dashboard" in codebase
├── Found: admin_views.py with AdminDashboardView
└── Identified: Uses IsAdminUser permission class

Step 2: Check permission implementation
├── Search: "IsAdminUser|permission_classes"
├── Found: DRF's IsAdminUser checks user.is_staff
└── Hypothesis: User might not have is_staff=True

Step 3: Verify user creation
├── Read: seed_admin.py management command
├── Found: Command sets is_staff=True correctly
└── Hypothesis refined: Issue is elsewhere

Step 4: Find actual error source
├── Search: "do not have permission to access this resource"
├── Found: middleware.py - RBACMiddleware
└── ROOT CAUSE IDENTIFIED: Custom middleware blocking request

Step 5: Analyze middleware logic
├── Read: middleware.py lines 74-84
├── Found: getattr(request.user, 'employee_profile', None)
├── Read: Employee model - OneToOneField with related_name='employee_profile'
└── BUG: getattr() doesn't catch DoesNotExist on reverse OneToOne relations
```

### Phase 3: Fix Implementation

**Problem:** Django OneToOne reverse relations raise `DoesNotExist` exception, not `None`

**Solution:** Replace `getattr()` with `try-except` block + superuser fallback

---

## Orchestration Pattern (Reusable)

```json
{
  "debugging_workflow": {
    "phase_1_understand": {
      "actions": [
        "Parse error message for HTTP status, endpoint, error text",
        "Identify frontend vs backend origin",
        "Note all file paths mentioned in stack trace"
      ],
      "tools": ["read_error_output"]
    },
    "phase_2_trace": {
      "actions": [
        "Find endpoint/route definition",
        "Identify middleware, decorators, permission classes",
        "Trace authentication flow",
        "Search for exact error message string in codebase"
      ],
      "tools": ["grep", "glob", "read_file"],
      "pattern": "work_backwards_from_error"
    },
    "phase_3_hypothesize": {
      "actions": [
        "Form hypothesis about root cause",
        "Verify by reading related code",
        "Refine hypothesis if evidence contradicts"
      ],
      "key_principle": "Never assume - always verify by reading code"
    },
    "phase_4_fix": {
      "actions": [
        "Make minimal targeted fix",
        "Check for same pattern elsewhere",
        "Update all instances"
      ],
      "key_principle": "Fix root cause, not symptoms"
    }
  }
}
```

---

## Skills Configuration for AI Debugging Agent

```json
{
  "agent_config": {
    "name": "debugging_agent",
    "capabilities": {
      "code_search": {
        "glob": "Find files by name pattern (*.py, **/views/*.py)",
        "grep": "Search file contents with regex",
        "priority": "Use grep to find error messages, function names, class names"
      },
      "code_reading": {
        "read_file": "Read file contents with line numbers",
        "rules": [
          "ALWAYS read a file before modifying it",
          "Read related files to understand context",
          "Follow imports to understand dependencies"
        ]
      },
      "code_modification": {
        "edit": "Make targeted replacements",
        "write": "Create new files (use sparingly)",
        "rules": [
          "Make minimal changes",
          "Don't refactor unrelated code",
          "Preserve existing patterns"
        ]
      }
    },
    "debugging_strategies": {
      "403_forbidden": [
        "1. Find the view/endpoint handling the URL",
        "2. Check permission_classes on the view",
        "3. Search for custom middleware that might intercept",
        "4. Search for the exact error message string",
        "5. Trace authentication token flow",
        "6. Verify user has required flags (is_staff, is_superuser)"
      ],
      "401_unauthorized": [
        "1. Check if token is being sent in headers",
        "2. Verify token format (Bearer prefix)",
        "3. Check token expiration settings",
        "4. Verify authentication backend configuration"
      ],
      "500_internal": [
        "1. Check server logs for stack trace",
        "2. Find the view and read the code",
        "3. Look for unhandled exceptions",
        "4. Check database queries and model relationships"
      ]
    }
  }
}
```

---

## Guardrails & Rules

```json
{
  "guardrails": {
    "before_any_edit": [
      "MUST read the file first",
      "MUST understand the surrounding context",
      "MUST identify all places the same pattern exists"
    ],
    "search_strategy": {
      "rule": "Start broad, then narrow",
      "example": [
        "First: grep for error message text",
        "Then: grep for function/class names found",
        "Then: read specific files identified"
      ]
    },
    "hypothesis_testing": {
      "rule": "Never assume - verify everything",
      "examples": [
        "Don't assume a function works as named - read it",
        "Don't assume config is correct - read it",
        "Don't assume user exists - verify creation code"
      ]
    },
    "fix_principles": [
      "Fix the root cause, not the symptom",
      "Make minimal changes",
      "Check for the same bug pattern elsewhere",
      "Don't add unnecessary error handling",
      "Don't refactor while debugging"
    ],
    "django_specific": {
      "onetoone_relations": "Reverse OneToOne access raises DoesNotExist, not None",
      "middleware_order": "Middleware runs in order - check MIDDLEWARE setting",
      "permission_classes": "DRF checks permissions after authentication",
      "is_staff_vs_is_superuser": "IsAdminUser checks is_staff, not is_superuser"
    }
  }
}
```

---

## Tool Usage Patterns

### Pattern 1: Find Where Error Originates
```
grep "exact error message text" -> identifies file
read file -> understand context
grep for function/class name -> find callers
```

### Pattern 2: Trace Permission Flow
```
grep "endpoint_path" -> find URL config
read urls.py -> find view class
read view -> find permission_classes
grep "permission class name" -> find implementation
grep "middleware" in settings -> find middleware stack
```

### Pattern 3: Understand Model Relationships
```
grep "class ModelName" -> find model definition
read model file -> check ForeignKey, OneToOneField, related_name
grep "related_name value" -> find usages
```

---

## Example Prompts for Debugging

### Initial Analysis Prompt
```
I have a [ERROR_TYPE] error. Here's the stack trace:
[STACK_TRACE]

Please:
1. Identify the endpoint and error message
2. Search the codebase for the endpoint definition
3. Trace the permission/authentication flow
4. Find where the error message originates
5. Identify the root cause
6. Propose a minimal fix
```

### Follow-up Pattern
```
After finding [FILE], please:
1. Read the file to understand the implementation
2. Search for related files that might have the same pattern
3. Verify any assumptions by reading the actual code
```

---

## Key Insights From This Debug Session

1. **Error messages are searchable** - The exact text "You do not have permission to access this resource" led directly to the middleware

2. **Custom code overrides framework behavior** - Even though DRF has `IsAdminUser`, the custom `RBACMiddleware` ran first and blocked the request

3. **Django ORM quirks matter** - `getattr(obj, 'reverse_relation', None)` doesn't work for OneToOne fields

4. **Multiple layers of auth** - This app had:
   - JWT Authentication (token validation)
   - DRF Permission Classes (IsAdminUser)
   - Custom RBAC Middleware (role-based)

5. **Fallback logic is important** - The fix added fallback to `is_superuser`/`is_staff` when employee profile doesn't exist

---

## Checklist for 403 Debugging

- [ ] Find the view handling the endpoint
- [ ] Check `permission_classes` on the view
- [ ] Search for custom middleware in MIDDLEWARE setting
- [ ] Search for the exact error message in codebase
- [ ] Verify user has required attributes (is_staff, is_superuser, roles)
- [ ] Check if token is being sent correctly
- [ ] Verify authentication backend can decode the token
- [ ] Check for CORS issues if cross-origin

---

## Debug Case #2: 404 Not Found + 500 Internal Server Error

### Error Analysis
**Errors:**
1. `GET /api/v2/hr/dashboard/ 404 (Not Found)` - Endpoint doesn't exist
2. `GET /api/v2/hr/employees/ 500 (Internal Server Error)` - AttributeError in repository

### Phase 1: Parse the Errors

**404 Error:**
- HTTP Status: 404 (Not Found)
- Endpoint: `/api/v2/hr/dashboard/`
- Meaning: The URL route doesn't exist in Django's URL configuration

**500 Error:**
- HTTP Status: 500 (Internal Server Error)
- Endpoint: `/api/v2/hr/employees/`
- Stack trace shows: `AttributeError: 'Employees' object has no attribute 'usd_salary'`
- Location: `employee_repository.py:233` in `_to_entity` method

### Phase 2: Systematic Tracing

```
For 404 Error:
├── Search: "hr/dashboard" in codebase
├── Found: Only in frontend service, NOT in backend urls.py
├── Read: hr/api/urls.py
└── CONFIRMED: No dashboard endpoint exists - needs to be created

For 500 Error:
├── Read stack trace: employee_repository.py line 233
├── Read file: _to_entity method accesses db_employee.usd_salary
├── Read: Employees model in models.py
├── Found: Model only has basic fields, missing salary fields
└── ROOT CAUSE: Repository expects fields that don't exist on model
```

### Phase 3: Fix Implementation

**404 Fix:**
1. Create `dashboard_views.py` with `HRDashboardView`
2. Add import to `views/__init__.py`
3. Add URL path in `urls.py`

**500 Fix:**
1. Add missing fields to `Employees` model:
   - `usd_salary`, `zig_salary` (DecimalField)
   - `national_id`, `phone`, `gender`, `marital_status`
   - `date_of_birth`, `date_joined`, `contract_from`, `contract_to`
   - Banking and statutory fields
2. Create and run migrations

### Migration Issues Encountered

**Problem 1: varchar_pattern_ops index on UUID**
```
psycopg.errors.DatatypeMismatch: operator class "varchar_pattern_ops"
does not accept data type uuid
```

**Root Cause:** PostgreSQL index created with `varchar_pattern_ops` is incompatible with UUID field type.

**Fix:** Add migration step to drop incompatible indexes before field type change:
```python
def drop_incompatible_indexes(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'table_name'
                AND indexdef LIKE '%varchar_pattern_ops%'
            """)
            for row in cursor.fetchall():
                cursor.execute(f'DROP INDEX IF EXISTS "{row[0]}"')
```

**Problem 2: Invalid UUID data**
```
psycopg.errors.InvalidTextRepresentation: invalid input syntax for type uuid: "UNKNOWN"
```

**Root Cause:** Existing data has non-UUID values (like "UNKNOWN" default) that can't be cast to UUID.

**Fix:** Add data cleanup step in migration:
```python
def fix_invalid_uuids(apps, schema_editor):
    Model = apps.get_model('app', 'Model')
    for obj in Model.objects.all():
        try:
            uuid.UUID(str(obj.uuid_field))
        except (ValueError, TypeError):
            obj.uuid_field = str(uuid.uuid4())
            obj.save()
```

---

## Checklist for 404 Debugging

- [ ] Verify the URL path in frontend matches backend expectation
- [ ] Check `urls.py` for the endpoint definition
- [ ] Check if view class exists and is imported
- [ ] Verify `app_name` matches URL namespace
- [ ] Check parent URL includes (`include('module.urls')`)
- [ ] Verify API prefix matches (`/api/v2/` vs `/api/v1/`)

---

## Checklist for 500 Debugging

- [ ] Read the full stack trace - note file and line number
- [ ] Go directly to the file:line mentioned
- [ ] Identify the exact attribute/method causing the error
- [ ] Check if model has all required fields
- [ ] Check if migrations are up to date
- [ ] Look for model-repository field mismatches
- [ ] Check for None/null handling issues

---

## Checklist for Migration Issues

- [ ] Check current migration state: `python manage.py showmigrations`
- [ ] For data type changes, check existing data compatibility
- [ ] For PostgreSQL, watch for index operator class mismatches
- [ ] Always backup database before complex migrations
- [ ] Use `RunPython` for data fixups before schema changes
- [ ] Test migrations on a copy of production data

---

## New Patterns Learned

### Pattern 4: Model-Repository Mismatch
```
Read stack trace -> find repository method
Read repository method -> list all model field accesses
Read model definition -> compare fields
Add missing fields to model
Create migrations
```

### Pattern 5: Missing Endpoint
```
Search backend for URL path -> not found
Check frontend expected URL
Read existing urls.py for patterns
Create view following existing patterns
Register in urls.py and __init__.py
```

### Pattern 6: Migration Data Conflicts
```
Run migration -> get data error
Identify conflicting data
Add RunPython step to fix data BEFORE schema change
Re-run migration
```

---

## Django/PostgreSQL Specific Knowledge

| Issue | Cause | Fix |
|-------|-------|-----|
| `varchar_pattern_ops` error | Changing CharField to UUIDField with existing index | Drop index before alter |
| `invalid input syntax for uuid` | Non-UUID data in field being converted | Clean data before alter |
| `DoesNotExist` on reverse relation | Using `getattr()` on OneToOne reverse | Use try-except |
| `RelatedObjectDoesNotExist` | Accessing missing related object | Check existence first |

---

## Key Insight: Repository Pattern Issues

When using Repository pattern with Django:
1. **Repository expects fields** that might not exist on the model
2. **Models evolve** but repositories might have outdated field references
3. **Always trace from error** to exact line, then verify model has that field
4. **Domain entities** might have more fields than the database model

---

## Debug Case #3: Value Object Type Mismatch

### Error Analysis
```
AttributeError: 'UUID' object has no attribute 'strip'
File: employee_repository.py, line 277
    employee_id=EmployeeId(db_employee.employee_id)
File: employee_id.py, line 57
    normalized = self.value.strip().upper()
```

### Root Cause
- Model field changed from `CharField` to `UUIDField`
- Value object (`EmployeeId`) expected string with `.strip()` method
- UUID objects don't have string methods

### Tracing Pattern
```
AttributeError: X has no attribute 'method'
    ↓
Find where value comes from (repository line)
    ↓
Check model field type (UUIDField)
    ↓
Check value object expectation (string with .strip())
    ↓
TYPE MISMATCH: UUID ≠ string
```

### Fix Applied
Update value object to handle both types:
```python
def __post_init__(self) -> None:
    raw_value = self.value
    # Handle UUID objects by converting to string
    if isinstance(raw_value, UUID):
        raw_value = str(raw_value)
        object.__setattr__(self, "value", raw_value)
    # Continue with string validation...
```

### Key Lesson
**When changing Django model field types:**
1. Check all value objects that consume that field
2. Check serializers that transform the data
3. Check repository methods that map model to entity
4. Update type handling in all layers

---

## Type Mismatch Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `'UUID' has no attribute 'strip'` | Passing UUID to string-expecting code | Convert with `str(uuid_obj)` |
| `'str' has no attribute 'hex'` | Passing string to UUID-expecting code | Convert with `UUID(str_val)` |
| `'NoneType' has no attribute X` | Optional field not checked | Add `if field:` guard |
| `'int' has no attribute 'split'` | Number field passed to string parser | Convert with `str(int_val)` |

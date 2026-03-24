# Leave Module

Leave management and approval workflow.

## Domain

### Aggregates

**LeaveType** (root):
- id, name
- default_days_allowed
- is_active

**LeaveBalance** (root):
- id, employee_id, leave_type_id
- year
- entitled_days, used_days, remaining_days

**LeaveRequest** (root):
- id, employee_id, leave_type_id
- start_date, end_date, days_count
- reason
- status (Pending, Approved, Rejected, Cancelled)
- requested_at, reviewed_by, reviewed_at

### Value Objects

- `LeaveStatus`: Pending, Approved, Rejected, Cancelled
- `LeavePeriod`: start, end, days

### Domain Services

- `LeaveBalanceCalculator`: Calculate remaining days
- `LeaveConflictDetector`: Check overlapping leaves
- `LeaveApprovalPolicy`: Approval rules

### Events

- `LeaveRequested`
- `LeaveApproved`
- `LeaveRejected`
- `LeaveCancelled`
- `LeaveBalanceAdjusted`

## Interfaces Exposed

```python
class ILeaveProvider(Protocol):
    def get_leave_balance(self, employee_id: int, year: int) -> list[LeaveBalanceDTO]: ...
    def get_leave_days_in_period(self, employee_id: int, start: date, end: date) -> int: ...
    def get_approved_leaves(self, employee_id: int, period: Period) -> list[LeaveDTO]: ...
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leave/types/` | List leave types |
| GET | `/api/leave/balances/` | Get balances |
| GET | `/api/leave/requests/` | List requests |
| POST | `/api/leave/requests/` | Submit request |
| POST | `/api/leave/requests/{id}/approve/` | Approve |
| POST | `/api/leave/requests/{id}/reject/` | Reject |

## Dependencies

- HR Module (IEmployeeProvider)
- Identity Module (ICurrentUserProvider)

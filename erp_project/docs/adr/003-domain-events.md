# ADR-003: Inter-Module Communication via Events

## Status

Accepted

## Context

Modules need to communicate. For example:
- When payroll is processed, accounting needs to create journal entries
- When an employee is hired, other modules may need to react
- When leave is approved, attendance records may need updating

Options for inter-module communication:

1. **Direct calls** - Module A calls Module B directly
2. **Shared database** - Modules read each other's tables
3. **Synchronous interfaces** - Module A calls Module B's interface
4. **Asynchronous events** - Module A publishes event, Module B subscribes

## Decision

We will use a **hybrid approach**:

### Synchronous Reads via Interfaces

For queries where Module A needs data from Module B:

```python
class IEmployeeProvider(Protocol):
    def get_employee(self, id: int) -> EmployeeDTO: ...
    def get_employee_salary(self, id: int) -> SalaryDTO: ...
```

- Payroll module depends on `IEmployeeProvider` interface
- HR module implements `IEmployeeProvider`
- Dependency injection provides the implementation

### Asynchronous Reactions via Domain Events

For side effects that don't need immediate response:

```python
# Payroll module publishes
event_bus.publish(PayrollProcessedEvent(period=period, payslips=payslips))

# Accounts module subscribes
@event_handler(PayrollProcessedEvent)
def create_salary_journal_entries(event: PayrollProcessedEvent):
    # Create accounting entries
```

### When to Use Each

| Scenario | Approach |
|----------|----------|
| Need data from another module | Interface |
| Trigger side effect in another module | Event |
| Real-time consistency required | Interface |
| Eventual consistency acceptable | Event |

## Consequences

### Positive

- Modules remain loosely coupled
- Clear contracts via interfaces
- Events decouple cause from effect
- Easy to add new subscribers without changing publisher
- Supports future extraction to microservices

### Negative

- Event handling adds complexity
- Debugging event chains can be tricky
- Must handle event ordering carefully
- Interface implementations must be provided

### Implementation Details

- In-process event bus (no external message queue yet)
- Events are processed synchronously within the request
- Future: can add async queue if needed
- Events are immutable value objects

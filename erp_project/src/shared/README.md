# Shared Kernel

Common building blocks used by all modules.

## Domain

### Value Objects (`domain/value_objects/`)

| Object | Purpose |
|--------|---------|
| `Money` | Financial amounts with currency |
| `DateRange` | Date periods with validation |
| `Period` | Payroll/reporting periods (year, month) |
| `Email` | Validated email address |
| `PhoneNumber` | Validated phone number |
| `NationalId` | Zimbabwe national ID |
| `EmployeeId` | EMP0001 format identifier |

### Base Classes (`domain/base/`)

| Class | Purpose |
|-------|---------|
| `Entity` | Base with ID and equality |
| `AggregateRoot` | Entity that owns consistency boundary |
| `ValueObject` | Immutable, equality by value |
| `DomainEvent` | Base for all domain events |

### Exceptions (`domain/exceptions/`)

| Exception | Purpose |
|-----------|---------|
| `DomainException` | Base for business rule violations |
| `ValidationException` | Invalid data |
| `NotFoundException` | Entity not found |
| `ConflictException` | Duplicate or conflict |

## Infrastructure

### Event Bus (`infrastructure/event_bus.py`)

In-process publish/subscribe for domain events. Modules communicate asynchronously through events.

### Unit of Work (`infrastructure/unit_of_work.py`)

Transaction management across repositories.

### Base Repository (`infrastructure/base_repository.py`)

Generic repository interface and base implementation.

## Usage

```python
from src.shared.domain.value_objects.money import Money
from src.shared.domain.base.entity import Entity
from src.shared.infrastructure.event_bus import EventBus

# Value objects are immutable
salary = Money(amount=1500, currency="USD")
new_salary = salary.add(Money(amount=200, currency="USD"))

# Entities have identity
class Employee(Entity):
    pass

# Events for module communication
event_bus = EventBus()
event_bus.publish(PayrollProcessedEvent(...))
```

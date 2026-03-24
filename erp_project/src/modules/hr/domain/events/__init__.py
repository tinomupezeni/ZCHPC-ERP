"""
HR domain events.
"""

from modules.hr.domain.events.employee_events import (
    ContractUpdatedEvent,
    DepartmentChangedEvent,
    EmployeeHiredEvent,
    EmployeeReactivatedEvent,
    EmployeeTerminatedEvent,
    EmployeeUpdatedEvent,
    PositionChangedEvent,
    SalaryChangedEvent,
)
from modules.hr.domain.events.organization_events import (
    DepartmentCreatedEvent,
    DepartmentDeletedEvent,
    DepartmentUpdatedEvent,
    PositionCreatedEvent,
    PositionDeletedEvent,
    PositionMovedEvent,
    PositionUpdatedEvent,
)

__all__ = [
    # Employee events
    "EmployeeHiredEvent",
    "EmployeeUpdatedEvent",
    "EmployeeTerminatedEvent",
    "EmployeeReactivatedEvent",
    "SalaryChangedEvent",
    "DepartmentChangedEvent",
    "PositionChangedEvent",
    "ContractUpdatedEvent",
    # Organization events
    "DepartmentCreatedEvent",
    "DepartmentUpdatedEvent",
    "DepartmentDeletedEvent",
    "PositionCreatedEvent",
    "PositionUpdatedEvent",
    "PositionDeletedEvent",
    "PositionMovedEvent",
]

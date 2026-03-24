"""
Shared infrastructure components.

Provides cross-cutting infrastructure concerns:
- Event bus for domain event publishing
- Unit of work for transaction management
- Base repository interfaces
"""

from shared.infrastructure.base_repository import (
    BaseRepository,
    IAggregateRepository,
    IReadRepository,
    IRepository,
    IWriteRepository,
    InMemoryRepository,
)
from shared.infrastructure.event_bus import (
    EventBus,
    get_event_bus,
    publish_event,
    subscribe_to,
)
from shared.infrastructure.unit_of_work import (
    DjangoUnitOfWork,
    IUnitOfWork,
    SyncUnitOfWork,
)

__all__ = [
    # Event Bus
    "EventBus",
    "get_event_bus",
    "publish_event",
    "subscribe_to",
    # Unit of Work
    "IUnitOfWork",
    "DjangoUnitOfWork",
    "SyncUnitOfWork",
    # Repositories
    "IRepository",
    "IReadRepository",
    "IWriteRepository",
    "IAggregateRepository",
    "BaseRepository",
    "InMemoryRepository",
]

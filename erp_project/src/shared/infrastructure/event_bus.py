"""
In-process Event Bus for domain event handling.

Provides publish/subscribe functionality for domain events,
enabling loose coupling between modules.

Example:
    # Register handler
    @event_bus.subscribe(PayrollProcessedEvent)
    def handle_payroll_processed(event: PayrollProcessedEvent):
        # Create accounting entries
        ...

    # Publish event
    event_bus.publish(PayrollProcessedEvent(period=period))
"""

import logging
from collections import defaultdict
from typing import Any, Callable, TypeVar

from shared.domain.base.domain_event import DomainEvent

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=DomainEvent)

# Type alias for event handlers
EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """
    In-process event bus for domain events.

    Provides synchronous event publishing and subscription.
    Events are processed in the order they are published.

    Usage:
        event_bus = EventBus()

        # Subscribe to events
        def on_employee_hired(event: EmployeeHiredEvent):
            print(f"Welcome {event.employee_name}!")

        event_bus.subscribe(EmployeeHiredEvent, on_employee_hired)

        # Or use decorator
        @event_bus.handler(PayrollProcessedEvent)
        def on_payroll_processed(event: PayrollProcessedEvent):
            # Create journal entries
            ...

        # Publish events
        event_bus.publish(EmployeeHiredEvent(employee_id=1, employee_name="John"))

    Thread Safety:
        This implementation is NOT thread-safe. For concurrent access,
        use appropriate synchronization or a thread-safe queue.

    Error Handling:
        By default, exceptions in handlers are logged but don't stop
        other handlers from running. Set strict_mode=True to propagate.
    """

    _instance: "EventBus | None" = None

    def __init__(self, strict_mode: bool = False) -> None:
        """
        Initialize the event bus.

        Args:
            strict_mode: If True, exceptions in handlers propagate immediately.
                        If False, exceptions are logged and other handlers continue.
        """
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)
        self._strict_mode = strict_mode
        self._published_events: list[DomainEvent] = []

    @classmethod
    def get_instance(cls) -> "EventBus":
        """
        Get the singleton instance of EventBus.

        Returns:
            The global EventBus instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None

    def subscribe(
        self,
        event_type: type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: The type of event to handle
            handler: Function to call when event is published
        """
        self._handlers[event_type].append(handler)  # type: ignore
        logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(
        self,
        event_type: type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> None:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event
            handler: The handler to remove
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)  # type: ignore
            logger.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")

    def handler(
        self,
        event_type: type[TEvent],
    ) -> Callable[[Callable[[TEvent], None]], Callable[[TEvent], None]]:
        """
        Decorator to subscribe a handler to an event type.

        Usage:
            @event_bus.handler(EmployeeHiredEvent)
            def on_employee_hired(event: EmployeeHiredEvent):
                ...
        """

        def decorator(func: Callable[[TEvent], None]) -> Callable[[TEvent], None]:
            self.subscribe(event_type, func)
            return func

        return decorator

    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all registered handlers.

        Args:
            event: The domain event to publish
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handlers")
        self._published_events.append(event)

        errors: list[Exception] = []

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception(f"Error in handler {handler.__name__} for {event_type.__name__}: {e}")
                if self._strict_mode:
                    raise
                errors.append(e)

        if errors and not self._strict_mode:
            logger.warning(f"{len(errors)} handler(s) failed for {event_type.__name__}")

    def publish_all(self, events: list[DomainEvent]) -> None:
        """
        Publish multiple events in order.

        Args:
            events: List of events to publish
        """
        for event in events:
            self.publish(event)

    def clear_handlers(self, event_type: type[DomainEvent] | None = None) -> None:
        """
        Clear handlers for an event type or all handlers.

        Args:
            event_type: Specific event type to clear, or None for all
        """
        if event_type is None:
            self._handlers.clear()
            logger.debug("Cleared all event handlers")
        else:
            self._handlers[event_type].clear()
            logger.debug(f"Cleared handlers for {event_type.__name__}")

    def get_handlers(self, event_type: type[DomainEvent]) -> list[EventHandler]:
        """
        Get all handlers for an event type.

        Args:
            event_type: The event type

        Returns:
            List of registered handlers
        """
        return self._handlers.get(event_type, []).copy()

    @property
    def published_events(self) -> list[DomainEvent]:
        """List of all events published through this bus."""
        return self._published_events.copy()

    def clear_published_events(self) -> None:
        """Clear the record of published events."""
        self._published_events.clear()


# Global event bus instance
def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return EventBus.get_instance()


def publish_event(event: DomainEvent) -> None:
    """Convenience function to publish an event to the global bus."""
    get_event_bus().publish(event)


def subscribe_to(
    event_type: type[TEvent],
) -> Callable[[Callable[[TEvent], None]], Callable[[TEvent], None]]:
    """
    Decorator to subscribe to events on the global bus.

    Usage:
        @subscribe_to(PayrollProcessedEvent)
        def handle_payroll(event: PayrollProcessedEvent):
            ...
    """
    return get_event_bus().handler(event_type)

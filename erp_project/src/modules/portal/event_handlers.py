"""
Event handlers that turn domain events from other modules into Notification
records (Slice 3: Purchase Request notifications).

This is the first real consumer of shared.infrastructure.event_bus in this
codebase - procurement publishes PurchaseRequestRejected/Processed after a
successful save (see purchase_request_use_cases.py), and this module reacts
by creating the requester's notification. Registered once at Django startup
by PortalConfig.ready(), the same "app config imports a module that wires
itself up at import time" shape as modules/hr/signals.py uses for Django
signals - here for the event bus instead, since procurement publishes domain
events rather than Django signals.

Deliberately depends on modules.procurement.domain.events (a stable, published
event contract) and nothing deeper in procurement - procurement itself has no
knowledge that portal or notifications exist, so this dependency runs one way.

Dual-write limitation: the handlers below run in a separate step after
procurement's own database write has already committed, with no outbox
tying the two together - see ProcessPurchaseRequestByProcurement's docstring
in purchase_request_use_cases.py for the full explanation of what that means
for a notification that goes missing (accepted for Slice 3, not fixed here).
"""

import logging

from modules.portal.domain.entities import Notification
from modules.portal.infrastructure.persistence.django_repositories import (
    DjangoNotificationRepository,
)
from modules.procurement.domain.events import (
    PurchaseRequestProcessed,
    PurchaseRequestRejected,
)
from shared.infrastructure import get_event_bus

logger = logging.getLogger(__name__)

_notification_repository = DjangoNotificationRepository()


def handle_purchase_request_rejected(event: PurchaseRequestRejected) -> None:
    notification = Notification.purchase_request_rejected(
        employee_id=event.requester_id,
        request_id=event.request_id,
        requisition_number=event.requisition_number,
        reason=event.reason,
    )
    _notification_repository.save(notification)
    logger.info(
        "Created purchase_request_rejected notification for employee %s (request %s)",
        event.requester_id,
        event.request_id,
    )


def handle_purchase_request_processed(event: PurchaseRequestProcessed) -> None:
    notification = Notification.purchase_request_processed(
        employee_id=event.requester_id,
        request_id=event.request_id,
        requisition_number=event.requisition_number,
    )
    _notification_repository.save(notification)
    logger.info(
        "Created purchase_request_processed notification for employee %s (request %s)",
        event.requester_id,
        event.request_id,
    )


def register() -> None:
    """
    Subscribe this module's handlers to the global event bus.

    Guarded against double-registration (checked by identity, not just
    presence) so calling this more than once - e.g. if Django's app registry
    is ever set up twice in the same process - can't fan a single published
    event out to the same handler multiple times, which would otherwise show
    up as duplicate notifications.
    """
    event_bus = get_event_bus()

    if handle_purchase_request_rejected not in event_bus.get_handlers(
        PurchaseRequestRejected
    ):
        event_bus.subscribe(PurchaseRequestRejected, handle_purchase_request_rejected)

    if handle_purchase_request_processed not in event_bus.get_handlers(
        PurchaseRequestProcessed
    ):
        event_bus.subscribe(PurchaseRequestProcessed, handle_purchase_request_processed)

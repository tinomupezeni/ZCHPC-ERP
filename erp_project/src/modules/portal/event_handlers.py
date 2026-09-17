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
    PurchaseRequestCorrectedAndResubmitted,
    PurchaseRequestProcessed,
    PurchaseRequestRejected,
)
from shared.infrastructure import get_event_bus

logger = logging.getLogger(__name__)

_notification_repository = DjangoNotificationRepository()


def _department_head_employee_id(department_id: int) -> int | None:
    """
    Resolve the recorded head of a department (F10's Department.head_id)
    directly against the HR model.

    Deliberately does not import modules.procurement's own
    DjangoOrganizationalDirectory, which reads this same field for
    department-head authorization - this module's own docstring commits to
    depending only on procurement's published events "and nothing deeper in
    procurement", so this reads the one HR field it needs directly instead
    of reusing a procurement-internal adapter.
    """
    from modules.hr.infrastructure.persistence.models import Department

    return (
        Department.objects.filter(pk=department_id)
        .values_list("head_id", flat=True)
        .first()
    )


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


def handle_purchase_request_corrected_and_resubmitted(
    event: PurchaseRequestCorrectedAndResubmitted,
) -> None:
    """
    F19: a rejected request corrected and resubmitted returns to
    PENDING_DEPARTMENT_HEAD via the normal submit flow (same status a
    first-time submission reaches) - the department head must be told
    explicitly that this is a correction awaiting re-approval, not a
    first-time submission, so they don't approve it on the assumption
    nothing has changed since they last looked at it.

    If the department currently has no recorded head, there is no one to
    notify. This is not treated as an error: matching the established,
    documented non-strict notification policy (see
    ProcessPurchaseRequestByProcurement's docstring - a missed notification
    must never undo or fail an already-successful workflow transition), the
    resubmission itself has already succeeded and stays successful; the gap
    is logged so it is visible operationally rather than silently dropped.
    """
    head_employee_id = _department_head_employee_id(event.department_id)
    if head_employee_id is None:
        logger.warning(
            "No department head recorded for department %s - skipping the "
            "corrected-and-resubmitted notification for request %s",
            event.department_id,
            event.request_id,
        )
        return

    notification = Notification.purchase_request_corrected(
        employee_id=head_employee_id,
        request_id=event.request_id,
        requisition_number=event.requisition_number,
    )
    _notification_repository.save(notification)
    logger.info(
        "Created purchase_request_corrected notification for department head %s (request %s)",
        head_employee_id,
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

    if handle_purchase_request_corrected_and_resubmitted not in event_bus.get_handlers(
        PurchaseRequestCorrectedAndResubmitted
    ):
        event_bus.subscribe(
            PurchaseRequestCorrectedAndResubmitted,
            handle_purchase_request_corrected_and_resubmitted,
        )

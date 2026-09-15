"""
Tests for modules.portal.event_handlers (Slice 3: Purchase Request notifications).

These are pure unit tests: the module-level `_notification_repository` is
patched with a Mock so no Django DB access is needed here - the real
DjangoNotificationRepository wiring is covered separately by the integration
tests in tests/integration/modules/procurement/.
"""

from unittest.mock import Mock

import pytest

from modules.portal import event_handlers
from modules.portal.domain.value_objects import NotificationType
from modules.procurement.domain.events import (
    PurchaseRequestProcessed,
    PurchaseRequestRejected,
)


@pytest.fixture
def notification_repository(monkeypatch):
    repo = Mock()
    monkeypatch.setattr(event_handlers, "_notification_repository", repo)
    return repo


class TestHandlePurchaseRequestRejected:
    def test_creates_a_notification_for_the_requester(self, notification_repository):
        event = PurchaseRequestRejected(
            request_id=42,
            requisition_number="PR-00042",
            requester_id=7,
            rejector_id=9,
            reason="Budget constraints",
        )

        event_handlers.handle_purchase_request_rejected(event)

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == 7
        assert notification.notification_type == NotificationType.PURCHASE_REQUEST_REJECTED
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == 42
        assert "PR-00042" in notification.message
        assert "Budget constraints" in notification.message

    def test_recipient_is_the_requester_not_the_rejector(self, notification_repository):
        """The department head/accounts/GM/director who rejects is never who gets notified."""
        event = PurchaseRequestRejected(
            request_id=1,
            requisition_number="PR-00001",
            requester_id=7,
            rejector_id=99,
            reason="No longer needed",
        )

        event_handlers.handle_purchase_request_rejected(event)

        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == 7
        assert notification.employee_id != 99


class TestHandlePurchaseRequestProcessed:
    def test_creates_a_notification_for_the_requester(self, notification_repository):
        event = PurchaseRequestProcessed(
            request_id=42,
            requisition_number="PR-00042",
            requester_id=7,
            processed_by=15,
        )

        event_handlers.handle_purchase_request_processed(event)

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == 7
        assert notification.notification_type == NotificationType.PURCHASE_REQUEST_PROCESSED
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == 42
        assert "PR-00042" in notification.message


class TestRegister:
    def test_subscribes_both_handlers_exactly_once_even_if_called_twice(self):
        """
        Guards against duplicate notifications from double app-registry setup
        (see event_handlers.register's docstring) - calling register() twice
        must not leave a handler subscribed twice.
        """
        from shared.infrastructure import get_event_bus

        bus = get_event_bus()
        bus.clear_handlers(PurchaseRequestRejected)
        bus.clear_handlers(PurchaseRequestProcessed)

        event_handlers.register()
        event_handlers.register()

        assert bus.get_handlers(PurchaseRequestRejected).count(
            event_handlers.handle_purchase_request_rejected
        ) == 1
        assert bus.get_handlers(PurchaseRequestProcessed).count(
            event_handlers.handle_purchase_request_processed
        ) == 1

        # Restore the real subscriptions the rest of the app relies on.
        event_handlers.register()

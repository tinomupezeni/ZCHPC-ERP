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
    PurchaseRequestAwaitingReview,
    PurchaseRequestCorrectedAndResubmitted,
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


@pytest.mark.django_db
class TestHandlePurchaseRequestCorrectedAndResubmitted:
    """
    F19: unlike Rejected/Processed, this handler must resolve a recipient
    (the department head) from the HR model - so, unlike the rest of this
    file, these tests need real Department/Employees rows rather than a bare
    Mock.
    """

    def _department_with_head(self, name="Test Department", head_email="head@example.com"):
        from modules.hr.infrastructure.persistence.models import Department, Employees

        head = Employees.objects.create(
            first_name="Hana", surname="Head", email=head_email
        )
        department = Department.objects.create(name=name, head=head)
        return department, head

    def test_creates_a_notification_for_the_departments_head(self, notification_repository):
        department, head = self._department_with_head()
        event = PurchaseRequestCorrectedAndResubmitted(
            request_id=42,
            requisition_number="PR-00042",
            requester_id=7,
            department_id=department.id,
        )

        event_handlers.handle_purchase_request_corrected_and_resubmitted(event)

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == head.id
        assert notification.notification_type == NotificationType.PURCHASE_REQUEST_CORRECTED
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == 42
        assert "PR-00042" in notification.message
        assert "corrected" in notification.message.lower()
        assert "re-approval" in notification.message.lower()

    def test_recipient_is_the_department_head_not_the_requester(self, notification_repository):
        """A requester cannot end up as their own correction's notification recipient."""
        department, head = self._department_with_head(
            name="Test Department 2", head_email="head2@example.com"
        )
        event = PurchaseRequestCorrectedAndResubmitted(
            request_id=1,
            requisition_number="PR-00001",
            requester_id=999,
            department_id=department.id,
        )

        event_handlers.handle_purchase_request_corrected_and_resubmitted(event)

        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == head.id
        assert notification.employee_id != 999

    def test_no_recorded_department_head_skips_the_notification_without_raising(
        self, notification_repository
    ):
        """
        Matches the existing non-strict notification policy (see
        ProcessPurchaseRequestByProcurement's docstring): a missing
        recipient must not raise - the resubmission it's reacting to has
        already succeeded and must stay successful either way.
        """
        from modules.hr.infrastructure.persistence.models import Department

        department = Department.objects.create(name="Headless Department")  # head is None

        event = PurchaseRequestCorrectedAndResubmitted(
            request_id=5,
            requisition_number="PR-00005",
            requester_id=7,
            department_id=department.id,
        )

        event_handlers.handle_purchase_request_corrected_and_resubmitted(event)

        notification_repository.save.assert_not_called()

    def test_nonexistent_department_skips_the_notification_without_raising(
        self, notification_repository
    ):
        event = PurchaseRequestCorrectedAndResubmitted(
            request_id=6,
            requisition_number="PR-00006",
            requester_id=7,
            department_id=999999,
        )

        event_handlers.handle_purchase_request_corrected_and_resubmitted(event)

        notification_repository.save.assert_not_called()


@pytest.mark.django_db
class TestHandlePurchaseRequestAwaitingReview:
    """
    F27: notify whoever needs to act at the stage a request just reached.

    Every branch here resolves a recipient from real HR rows (Department, or
    Employees/Role for the permission-holding stages), so - like
    TestHandlePurchaseRequestCorrectedAndResubmitted above - these need
    django_db rather than a bare Mock.
    """

    def _department_with_head(self, name="F27 Department", head_email="f27head@example.com"):
        from modules.hr.infrastructure.persistence.models import Department, Employees

        head = Employees.objects.create(
            first_name="Hana", surname="Head", email=head_email
        )
        department = Department.objects.create(name=name, head=head)
        return department, head

    def _employee_with_permissions(self, name, permissions, *, is_active=True):
        from modules.hr.infrastructure.persistence.models import Employees, Role

        role = Role.objects.create(
            name=f"F27_{name.upper().replace(' ', '_')}",
            permissions=list(permissions),
        )
        return Employees.objects.create(
            first_name=name.split()[0],
            surname=name.split()[-1],
            email=f"{name.lower().replace(' ', '.')}@example.com",
            role=role,
            is_active=is_active,
        )

    def _event(
        self,
        new_status,
        department_id=1,
        request_id=42,
        requisition_number="PR-00042",
    ):
        return PurchaseRequestAwaitingReview(
            request_id=request_id,
            requisition_number=requisition_number,
            new_status=new_status,
            department_id=department_id,
        )

    # ---------------------------------------------------------------
    # PENDING_DEPARTMENT_HEAD - resolved by department, same as F19's
    # corrected-and-resubmitted recipient.
    # ---------------------------------------------------------------

    def test_department_head_stage_notifies_the_departments_recorded_head(
        self, notification_repository
    ):
        department, head = self._department_with_head()

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_DEPARTMENT_HEAD", department_id=department.id)
        )

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == head.id
        assert (
            notification.notification_type
            == NotificationType.PURCHASE_REQUEST_AWAITING_DEPARTMENT_HEAD
        )
        assert notification.related_object_type == "purchase_request"
        assert notification.related_object_id == 42
        assert "PR-00042" in notification.message
        assert "Department Head" in notification.title

    def test_department_head_stage_skips_without_raising_when_no_head_is_recorded(
        self, notification_repository
    ):
        from modules.hr.infrastructure.persistence.models import Department

        department = Department.objects.create(name="Headless F27 Department")

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_DEPARTMENT_HEAD", department_id=department.id)
        )

        notification_repository.save.assert_not_called()

    # ---------------------------------------------------------------
    # Permission-holding stages: Accounts / GM / Director / Procurement.
    # ---------------------------------------------------------------

    def test_accounts_stage_notifies_every_current_holder_of_the_permission(
        self, notification_repository
    ):
        """Multiple accountants -> one notification row each, not one shared row."""
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        adam = self._employee_with_permissions("Adam Accounts", [P.ACCOUNTS_VERIFY])
        anna = self._employee_with_permissions("Anna Accounts", [P.ACCOUNTS_VERIFY])
        gina = self._employee_with_permissions("Gina Manager", [P.GM_RECOMMEND])

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_ACCOUNTS")
        )

        assert notification_repository.save.call_count == 2
        recipients = {
            call.args[0].employee_id
            for call in notification_repository.save.call_args_list
        }
        assert recipients == {adam.id, anna.id}
        assert gina.id not in recipients  # no cross-role notification
        for call in notification_repository.save.call_args_list:
            assert (
                call.args[0].notification_type
                == NotificationType.PURCHASE_REQUEST_AWAITING_ACCOUNTS
            )

    def test_accounts_stage_recognises_a_wildcard_permission_grant(
        self, notification_repository
    ):
        """A role granted "procurement.*" must count, matching the API's own RBAC check."""
        wildcard_holder = self._employee_with_permissions(
            "Wanda Wildcard", ["procurement.*"]
        )

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_ACCOUNTS")
        )

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == wildcard_holder.id

    def test_gm_stage_notifies_only_gm_holders_not_accounts_holders(
        self, notification_repository
    ):
        """No cross-role notification: an Accounts holder must never get a GM-stage notice."""
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        gina = self._employee_with_permissions("Gina Manager", [P.GM_RECOMMEND])
        self._employee_with_permissions("Adam Accounts", [P.ACCOUNTS_VERIFY])

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_GM")
        )

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == gina.id
        assert (
            notification.notification_type == NotificationType.PURCHASE_REQUEST_AWAITING_GM
        )

    def test_director_stage_notifies_director_holders(self, notification_repository):
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        dana = self._employee_with_permissions("Dana Director", [P.DIRECTOR_APPROVE])
        self._employee_with_permissions("Pat Procure", [P.PROCESS])

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_DIRECTOR")
        )

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == dana.id
        assert (
            notification.notification_type
            == NotificationType.PURCHASE_REQUEST_AWAITING_DIRECTOR
        )

    def test_procurement_stage_notifies_procurement_holders(
        self, notification_repository
    ):
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        pat = self._employee_with_permissions("Pat Procure", [P.PROCESS])
        self._employee_with_permissions("Dana Director", [P.DIRECTOR_APPROVE])

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_PROCUREMENT")
        )

        notification_repository.save.assert_called_once()
        (notification,), _ = notification_repository.save.call_args
        assert notification.employee_id == pat.id
        assert (
            notification.notification_type
            == NotificationType.PURCHASE_REQUEST_AWAITING_PROCUREMENT
        )

    def test_an_inactive_employee_is_excluded_even_with_a_matching_permission(
        self, notification_repository
    ):
        from modules.procurement.application.authorization import (
            PurchaseRequestPermissions as P,
        )

        self._employee_with_permissions(
            "Ines Inactive", [P.ACCOUNTS_VERIFY], is_active=False
        )

        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_ACCOUNTS")
        )

        notification_repository.save.assert_not_called()

    def test_no_current_permission_holder_skips_without_raising(
        self, notification_repository
    ):
        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PENDING_ACCOUNTS")
        )

        notification_repository.save.assert_not_called()

    def test_an_unrecognised_status_skips_without_raising(self, notification_repository):
        event_handlers.handle_purchase_request_awaiting_review(
            self._event("PROCESSED")
        )

        notification_repository.save.assert_not_called()


class TestRegister:
    def test_subscribes_every_handler_exactly_once_even_if_called_twice(self):
        """
        Guards against duplicate notifications from double app-registry setup
        (see event_handlers.register's docstring) - calling register() twice
        must not leave a handler subscribed twice.
        """
        from shared.infrastructure import get_event_bus

        bus = get_event_bus()
        bus.clear_handlers(PurchaseRequestRejected)
        bus.clear_handlers(PurchaseRequestProcessed)
        bus.clear_handlers(PurchaseRequestCorrectedAndResubmitted)
        bus.clear_handlers(PurchaseRequestAwaitingReview)

        event_handlers.register()
        event_handlers.register()

        assert bus.get_handlers(PurchaseRequestRejected).count(
            event_handlers.handle_purchase_request_rejected
        ) == 1
        assert bus.get_handlers(PurchaseRequestProcessed).count(
            event_handlers.handle_purchase_request_processed
        ) == 1
        assert bus.get_handlers(PurchaseRequestCorrectedAndResubmitted).count(
            event_handlers.handle_purchase_request_corrected_and_resubmitted
        ) == 1
        assert bus.get_handlers(PurchaseRequestAwaitingReview).count(
            event_handlers.handle_purchase_request_awaiting_review
        ) == 1

        # Restore the real subscriptions the rest of the app relies on.
        event_handlers.register()

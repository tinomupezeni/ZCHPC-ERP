"""
Django repository implementations for portal-specific entities.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from modules.portal.domain.entities import (
    ExpenseClaim,
    SupportTicket,
    TicketMessage,
    Notification,
    Document,
    DocumentCategory,
)
from modules.portal.domain.value_objects import (
    ExpenseStatus,
    TicketStatus,
    TicketCategory,
    TicketPriority,
    NotificationType,
    DocumentVisibility,
)
from modules.portal.application.interfaces import (
    IExpenseClaimRepository,
    ISupportTicketRepository,
    INotificationRepository,
    IDocumentRepository,
    IDocumentCategoryRepository,
    IExpenseCategoryRepository,
    IQRTokenRepository,
)


class DjangoExpenseClaimRepository(IExpenseClaimRepository):
    """Django repository for expense claims."""

    def _to_domain(self, model) -> ExpenseClaim:
        return ExpenseClaim(
            id=model.id,
            employee_id=model.employee_id,
            category_id=model.category_id,
            title=model.title,
            description=model.description,
            amount=model.amount,
            currency=model.currency,
            date_incurred=model.date_incurred,
            receipt_path=model.receipt.name if model.receipt else None,
            status=ExpenseStatus(model.status.replace(" ", "")),
            submitted_at=model.submitted_at,
            reviewed_by=model.reviewed_by_id,
            reviewed_at=model.reviewed_at,
            review_notes=model.review_notes,
            paid_at=model.paid_at,
            payment_reference=model.payment_reference,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def save(self, claim: ExpenseClaim) -> ExpenseClaim:
        from employee_portal.models import ExpenseClaim as ExpenseClaimModel

        if claim.id:
            model = ExpenseClaimModel.objects.get(pk=claim.id)
        else:
            model = ExpenseClaimModel()

        model.employee_id = claim.employee_id
        model.category_id = claim.category_id
        model.title = claim.title
        model.description = claim.description
        model.amount = claim.amount
        model.currency = claim.currency
        model.date_incurred = claim.date_incurred
        model.status = claim.status.value
        model.submitted_at = claim.submitted_at
        model.reviewed_by_id = claim.reviewed_by
        model.reviewed_at = claim.reviewed_at
        model.review_notes = claim.review_notes
        model.paid_at = claim.paid_at
        model.payment_reference = claim.payment_reference
        model.save()

        return self._to_domain(model)

    def get_by_id(self, claim_id: int) -> Optional[ExpenseClaim]:
        from employee_portal.models import ExpenseClaim as ExpenseClaimModel
        try:
            model = ExpenseClaimModel.objects.get(pk=claim_id)
            return self._to_domain(model)
        except ExpenseClaimModel.DoesNotExist:
            return None

    def get_by_employee(
        self,
        employee_id: int,
        status: Optional[ExpenseStatus] = None,
    ) -> List[ExpenseClaim]:
        from employee_portal.models import ExpenseClaim as ExpenseClaimModel

        queryset = ExpenseClaimModel.objects.filter(
            employee_id=employee_id,
        ).order_by("-created_at")

        if status:
            queryset = queryset.filter(status=status.value)

        return [self._to_domain(m) for m in queryset]

    def get_pending_review(self) -> List[ExpenseClaim]:
        from employee_portal.models import ExpenseClaim as ExpenseClaimModel

        queryset = ExpenseClaimModel.objects.filter(
            status__in=["Submitted", "Under Review"],
        ).order_by("submitted_at")

        return [self._to_domain(m) for m in queryset]

    def delete(self, claim_id: int) -> bool:
        from employee_portal.models import ExpenseClaim as ExpenseClaimModel
        try:
            model = ExpenseClaimModel.objects.get(
                pk=claim_id,
                status="Draft",
            )
            model.delete()
            return True
        except ExpenseClaimModel.DoesNotExist:
            return False


class DjangoNotificationRepository(INotificationRepository):
    """Django repository for notifications."""

    def _to_domain(self, model) -> Notification:
        return Notification(
            id=model.id,
            employee_id=model.employee_id,
            notification_type=NotificationType(model.notification_type),
            title=model.title,
            message=model.message,
            is_read=model.is_read,
            read_at=model.read_at,
            related_object_type=model.related_object_type,
            related_object_id=model.related_object_id,
            created_at=model.created_at,
        )

    def save(self, notification: Notification) -> Notification:
        from employee_portal.models import Notification as NotificationModel

        if notification.id:
            model = NotificationModel.objects.get(pk=notification.id)
        else:
            model = NotificationModel()

        model.employee_id = notification.employee_id
        model.notification_type = notification.notification_type.value
        model.title = notification.title
        model.message = notification.message
        model.is_read = notification.is_read
        model.read_at = notification.read_at
        model.related_object_type = notification.related_object_type
        model.related_object_id = notification.related_object_id
        model.save()

        return self._to_domain(model)

    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        from employee_portal.models import Notification as NotificationModel
        try:
            model = NotificationModel.objects.get(pk=notification_id)
            return self._to_domain(model)
        except NotificationModel.DoesNotExist:
            return None

    def get_by_employee(
        self,
        employee_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        from employee_portal.models import Notification as NotificationModel

        queryset = NotificationModel.objects.filter(
            employee_id=employee_id,
        ).order_by("-created_at")

        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)

        if notification_type:
            queryset = queryset.filter(notification_type=notification_type.value)

        return [self._to_domain(m) for m in queryset]

    def get_unread_count(self, employee_id: int) -> int:
        from employee_portal.models import Notification as NotificationModel
        return NotificationModel.objects.filter(
            employee_id=employee_id,
            is_read=False,
        ).count()

    def mark_all_read(self, employee_id: int) -> int:
        from employee_portal.models import Notification as NotificationModel
        return NotificationModel.objects.filter(
            employee_id=employee_id,
            is_read=False,
        ).update(is_read=True, read_at=datetime.now())


class DjangoQRTokenRepository(IQRTokenRepository):
    """Django repository for QR tokens."""

    def get_current_token(self) -> Optional[str]:
        from employee_portal.models import AttendanceQRToken

        now = datetime.now()
        try:
            token = AttendanceQRToken.objects.get(
                is_active=True,
                expires_at__gt=now,
            )
            return token.token
        except AttendanceQRToken.DoesNotExist:
            return None

    def create_token(self, token: str, expires_at: datetime) -> None:
        from employee_portal.models import AttendanceQRToken

        # Deactivate existing tokens
        AttendanceQRToken.objects.filter(is_active=True).update(is_active=False)

        # Create new token
        AttendanceQRToken.objects.create(
            token=token,
            expires_at=expires_at,
            is_active=True,
            used_count=0,
        )

    def verify_token(self, token: str) -> bool:
        from employee_portal.models import AttendanceQRToken

        now = datetime.now()
        return AttendanceQRToken.objects.filter(
            token=token,
            is_active=True,
            expires_at__gt=now,
        ).exists()

    def increment_usage(self, token: str) -> None:
        from employee_portal.models import AttendanceQRToken
        from django.db.models import F

        AttendanceQRToken.objects.filter(token=token).update(
            used_count=F("used_count") + 1
        )


class DjangoExpenseCategoryRepository(IExpenseCategoryRepository):
    """Django repository for expense categories."""

    def get_all(self, include_inactive: bool = False) -> List[dict]:
        from employee_portal.models import ExpenseCategory

        queryset = ExpenseCategory.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)

        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "is_active": c.is_active,
                "max_amount": c.max_amount,
                "requires_receipt": c.requires_receipt,
            }
            for c in queryset
        ]

    def get_by_id(self, category_id: int) -> Optional[dict]:
        from employee_portal.models import ExpenseCategory
        try:
            c = ExpenseCategory.objects.get(pk=category_id)
            return {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "is_active": c.is_active,
                "max_amount": c.max_amount,
                "requires_receipt": c.requires_receipt,
            }
        except ExpenseCategory.DoesNotExist:
            return None

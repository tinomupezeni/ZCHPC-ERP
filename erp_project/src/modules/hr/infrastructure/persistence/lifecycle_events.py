"""
Writes employee lifecycle events (AUD-02).

The only writer of hr.EmployeeLifecycleEvent; EmployeeLifecycleService calls
it inside the transaction that makes the change. There is no update or
delete here, and the model refuses both.
"""

from modules.hr.infrastructure.persistence.models import EmployeeLifecycleEvent


class DjangoLifecycleEventRecorder:
    def record(
        self,
        *,
        employee_id: int,
        employee_number: str,
        event_type: str,
        from_status: str,
        to_status: str,
        actor_user_id=None,
        reason: str = "",
        source: str = "",
        details: dict | None = None,
    ) -> EmployeeLifecycleEvent:
        actor_email = ""
        if actor_user_id is not None:
            from modules.identity.infrastructure.persistence.models import CustomUser

            actor_email = (
                CustomUser.objects.filter(pk=actor_user_id).values_list("email", flat=True).first()
                or ""
            )
        return EmployeeLifecycleEvent.objects.create(
            employee_id=employee_id,
            employee_number=employee_number,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_user_id,
            actor_email=actor_email,
            reason=reason or "",
            source=source or "",
            details=details or {},
        )

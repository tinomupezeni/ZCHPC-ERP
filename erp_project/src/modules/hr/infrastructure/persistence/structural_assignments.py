"""
Structural authority an employee holds, as far as archiving is concerned
(AUD-02).

The one structural authority with runtime effect is Department.head: it is
the department-head approver for purchase requests (procurement resolves it
at decision time). Archiving must never leave an archived employee as a
department's head, and must never strand approvals waiting on them.

reports_to carries no runtime authority anywhere in the application and is
left as recorded; other references to an employee are history.
"""

from modules.hr.infrastructure.persistence.models import Department

# A purchase request at this stage is waiting for its department's head.
PENDING_DEPARTMENT_HEAD = "PENDING_DEPARTMENT_HEAD"


class DjangoStructuralAssignments:
    """Reads and releases an employee's department headships."""

    def departments_headed_by(self, employee_id: int, lock: bool = True) -> list[int]:
        """
        Ids of the departments this employee heads, row-locked until the
        surrounding transaction ends so no headship changes under the caller.

        ``lock=False`` is a plain read, for callers that only report the
        headships (the caller's own access summary) and hold no transaction.
        """
        departments = Department.objects.select_for_update() if lock else Department.objects
        return list(
            departments.filter(head_id=employee_id)
            .order_by("pk")
            .values_list("pk", flat=True)
        )

    def pending_department_head_approvals(self, department_ids: list[int]) -> list[int]:
        """Ids of purchase requests in these departments awaiting the head."""
        from modules.procurement.infrastructure.persistence.models import PurchaseRequest

        return list(
            PurchaseRequest.objects.filter(
                department_id__in=department_ids, status=PENDING_DEPARTMENT_HEAD
            )
            .order_by("pk")
            .values_list("pk", flat=True)
        )

    def vacate_department_headships(self, employee_id: int) -> None:
        """Leave every department this employee heads without a head."""
        Department.objects.filter(head_id=employee_id).update(head=None)

"""Django persistence models for the workflow module."""

from django.db import models


class Workflow(models.Model):
    """One approval chain per document type; at most one active."""

    name = models.CharField(max_length=120, unique=True)
    document_type = models.CharField(
        max_length=120,
        help_text="E.g. procurement.PurchaseRequest - the governed record.",
    )
    is_active = models.BooleanField(default=True)
    state_field = models.CharField(
        max_length=64,
        default="status",
        help_text="Record attribute holding the current state value.",
    )

    class Meta:
        db_table = "workflow_workflow"
        constraints = [
            models.UniqueConstraint(
                fields=["document_type"],
                condition=models.Q(is_active=True),
                name="one_active_workflow_per_doctype",
            )
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.document_type})"


class WorkflowState(models.Model):
    """One named step in a chain."""

    workflow = models.ForeignKey(Workflow, related_name="states", on_delete=models.CASCADE)
    state = models.CharField(max_length=64)

    class Meta:
        db_table = "workflow_workflowstate"
        unique_together = [("workflow", "state")]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.workflow.name}: {self.state}"


class WorkflowTransition(models.Model):
    """One labeled action between two states."""

    workflow = models.ForeignKey(Workflow, related_name="transitions", on_delete=models.CASCADE)
    action = models.CharField(max_length=64, help_text="Machine name, e.g. approve.")
    label = models.CharField(max_length=64, help_text="UI copy, e.g. Approve.")
    state = models.CharField(max_length=64)
    next_state = models.CharField(max_length=64)
    required_permissions = models.JSONField(
        default=list,
        help_text="Every capability the actor must hold.",
    )
    allow_self_approval = models.BooleanField(default=False)

    class Meta:
        db_table = "workflow_workflowtransition"
        unique_together = [("workflow", "state", "action")]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.workflow.name}: {self.state} --{self.action}--> {self.next_state}"


class WorkflowCondition(models.Model):
    """One structured predicate gating a transition (no expressions)."""

    transition = models.ForeignKey(WorkflowTransition, related_name="conditions", on_delete=models.CASCADE)
    field = models.CharField(max_length=64)
    operator = models.CharField(
        max_length=8,
        help_text="One of eq, ne, gt, gte, lt, lte, in, not_in.",
    )
    value = models.JSONField(help_text="Compared value; list for in/not_in.")

    class Meta:
        db_table = "workflow_workflowcondition"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.transition} when {self.field} {self.operator} {self.value}"


class WorkflowAction(models.Model):
    """Audit/inbox row: who moved what, when. Open rows are the queue."""

    voucher_type = models.CharField(max_length=120)
    voucher_id = models.CharField(max_length=64)
    state = models.CharField(max_length=64, help_text="State entered by the recorded action.")
    action = models.CharField(max_length=64)
    status = models.CharField(max_length=16, default="Open")
    completed_by = models.ForeignKey(
        "identity.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_workflowaction"
        indexes = [
            models.Index(fields=["voucher_type", "voucher_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.voucher_type}#{self.voucher_id} {self.action} ({self.status})"

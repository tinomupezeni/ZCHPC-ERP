"""
Seed the purchase-request approval chain as workflow rows (pilot).

Mirrors the transitions the PurchaseRequest aggregate and
PurchaseRequestAuthorizationPolicy already enforce - submit, four
offices, procurement processing, rejection, and correction - so the
engine resolves exactly the actions execution allows. Self-approval is
forbidden on every stage, matching _require_not_requester. No document
data is touched: statuses keep their values, so in-flight requests need
no migration.

Reversible: removes the seeded chain and its rows.
"""

from django.db import migrations


WORKFLOW_NAME = "Purchase Request Approval"
DOCUMENT_TYPE = "procurement.PurchaseRequest"

STATES = [
    "DRAFT",
    "PENDING_DEPARTMENT_HEAD",
    "PENDING_ACCOUNTS",
    "PENDING_GM",
    "PENDING_DIRECTOR",
    "PENDING_PROCUREMENT",
    "PROCESSED",
    "REJECTED",
]

# (state, action, label, next_state, required_permissions)
TRANSITIONS = [
    ("DRAFT", "submit", "Submit", "PENDING_DEPARTMENT_HEAD", ["procurement.purchase_request.submit"]),
    (
        "PENDING_DEPARTMENT_HEAD",
        "approve",
        "Approve",
        "PENDING_ACCOUNTS",
        ["procurement.purchase_request.department_head_approve"],
    ),
    ("PENDING_DEPARTMENT_HEAD", "reject", "Reject", "REJECTED", ["procurement.purchase_request.reject"]),
    ("PENDING_ACCOUNTS", "verify", "Verify", "PENDING_GM", ["procurement.purchase_request.accounts_verify"]),
    ("PENDING_ACCOUNTS", "reject", "Reject", "REJECTED", ["procurement.purchase_request.reject"]),
    ("PENDING_GM", "recommend", "Recommend", "PENDING_DIRECTOR", ["procurement.purchase_request.gm_recommend"]),
    ("PENDING_GM", "reject", "Reject", "REJECTED", ["procurement.purchase_request.reject"]),
    (
        "PENDING_DIRECTOR",
        "approve",
        "Approve",
        "PENDING_PROCUREMENT",
        ["procurement.purchase_request.director_approve"],
    ),
    ("PENDING_DIRECTOR", "reject", "Reject", "REJECTED", ["procurement.purchase_request.reject"]),
    ("PENDING_PROCUREMENT", "process", "Process", "PROCESSED", ["procurement.purchase_request.process"]),
    (
        "REJECTED",
        "correct-resubmit",
        "Correct & resubmit",
        "DRAFT",
        ["procurement.purchase_request.correct", "procurement.purchase_request.resubmit"],
    ),
]


def seed_purchase_request_workflow(apps, schema_editor):
    Workflow = apps.get_model("workflow", "Workflow")
    WorkflowState = apps.get_model("workflow", "WorkflowState")
    WorkflowTransition = apps.get_model("workflow", "WorkflowTransition")

    workflow, _ = Workflow.objects.update_or_create(
        name=WORKFLOW_NAME,
        defaults={"document_type": DOCUMENT_TYPE, "is_active": True},
    )
    for state in STATES:
        WorkflowState.objects.get_or_create(workflow=workflow, state=state)
    for state, action, label, next_state, permissions in TRANSITIONS:
        WorkflowTransition.objects.update_or_create(
            workflow=workflow,
            state=state,
            action=action,
            defaults={
                "label": label,
                "next_state": next_state,
                "required_permissions": permissions,
                "allow_self_approval": False,
            },
        )


def unseed_purchase_request_workflow(apps, schema_editor):
    Workflow = apps.get_model("workflow", "Workflow")
    Workflow.objects.filter(name=WORKFLOW_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_purchase_request_workflow,
            unseed_purchase_request_workflow,
        ),
    ]

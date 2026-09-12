"""
Purchase Request capabilities (RBAC permission strings).

These extend the existing permission representation used across the system:

    - permissions are dotted strings matched by
      ``modules.identity.domain.value_objects.Permission``
    - a role's granted permissions live in ``hr.Role.permissions`` (JSON list)
      and are loaded into an identity ``Role``/``PermissionSet`` by
      ``DjangoRoleRepository``

No new authorization framework is introduced here - only the capability
vocabulary that the Purchase Request workflow needs.

Note on wildcards: the existing ``Permission`` semantics mean a role granted
``procurement.*`` is granted every capability below. Roles that should only
hold part of the workflow must be granted the explicit strings.
"""


class PurchaseRequestPermissions:
    """Capability strings for the Purchase Request workflow."""

    CREATE = "procurement.purchase_request.create"
    VIEW = "procurement.purchase_request.view"
    SUBMIT = "procurement.purchase_request.submit"

    DEPARTMENT_HEAD_APPROVE = "procurement.purchase_request.department_head_approve"
    ACCOUNTS_VERIFY = "procurement.purchase_request.accounts_verify"
    GM_RECOMMEND = "procurement.purchase_request.gm_recommend"
    DIRECTOR_APPROVE = "procurement.purchase_request.director_approve"

    REJECT = "procurement.purchase_request.reject"
    CORRECT = "procurement.purchase_request.correct"
    RESUBMIT = "procurement.purchase_request.resubmit"

    PROCESS = "procurement.purchase_request.process"

    @classmethod
    def all(cls) -> list[str]:
        """Every Purchase Request capability."""
        return [
            cls.CREATE,
            cls.VIEW,
            cls.SUBMIT,
            cls.DEPARTMENT_HEAD_APPROVE,
            cls.ACCOUNTS_VERIFY,
            cls.GM_RECOMMEND,
            cls.DIRECTOR_APPROVE,
            cls.REJECT,
            cls.CORRECT,
            cls.RESUBMIT,
            cls.PROCESS,
        ]


# Capabilities every requester needs to raise and maintain their own request.
_REQUESTER_PERMISSIONS = [
    PurchaseRequestPermissions.CREATE,
    PurchaseRequestPermissions.VIEW,
    PurchaseRequestPermissions.SUBMIT,
    PurchaseRequestPermissions.CORRECT,
    PurchaseRequestPermissions.RESUBMIT,
]


# Suggested provisioning defaults for the role names that already exist in
# ``modules.identity.domain.value_objects.RoleName``.
#
# This is a seed/reference map for populating ``hr.Role.permissions``; it is
# deliberately NOT consulted at authorization time. Authorization always reads
# the permissions actually granted to the actor's role, so grants stay a data
# decision rather than a hard-coded one.
#
# GENERAL_MANAGER and DIRECTOR are absent because no such role exists in the
# current role vocabulary - see the Slice 4 organizational gaps.
DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "REGULAR_STAFF": list(_REQUESTER_PERMISSIONS),
    "INTERN": list(_REQUESTER_PERMISSIONS),
    "DEPARTMENT_MANAGER": [
        *_REQUESTER_PERMISSIONS,
        PurchaseRequestPermissions.DEPARTMENT_HEAD_APPROVE,
        PurchaseRequestPermissions.REJECT,
    ],
    "ACCOUNTANT": [
        *_REQUESTER_PERMISSIONS,
        PurchaseRequestPermissions.ACCOUNTS_VERIFY,
        PurchaseRequestPermissions.REJECT,
    ],
    "PROCUREMENT_OFFICER": [
        *_REQUESTER_PERMISSIONS,
        PurchaseRequestPermissions.PROCESS,
    ],
    "HUMAN_RESOURCES": list(_REQUESTER_PERMISSIONS),
    "SALES_REPRESENTATIVE": list(_REQUESTER_PERMISSIONS),
}

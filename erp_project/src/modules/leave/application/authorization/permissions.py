"""
Leave capability identifiers (RBAC permission vocabulary).

Dotted strings matched by ``modules.identity.domain.value_objects.Permission``
and granted to roles through ``hr.Role.permissions`` by system administrators.
Which roles hold them is an administrator decision; nothing here assigns them.

An employee's access to their *own* leave requests and balances is not a
capability - it follows from being that employee. These capabilities cover
acting on other employees' leave data and on leave configuration.

Existing wildcard semantics are unchanged: ``leave.*`` or ``*`` satisfies
every capability below.
"""


class LeavePermissions:
    """Capability strings for leave operations."""

    REQUEST_VIEW_ANY = "leave.request.view_any"
    REQUEST_REVIEW = "leave.request.review"
    REQUEST_CANCEL_ANY = "leave.request.cancel_any"

    BALANCE_VIEW_ANY = "leave.balance.view_any"
    BALANCE_MANAGE = "leave.balance.manage"

    TYPE_MANAGE = "leave.type.manage"

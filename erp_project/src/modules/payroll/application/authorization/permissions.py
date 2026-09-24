"""
Payroll capability identifiers (RBAC permission vocabulary).

These are *identifiers only*. They follow the dotted-string convention already
used by procurement (``procurement.purchase_request.*``) and HR
(``hr.role.manage``), are matched by
``modules.identity.domain.value_objects.Permission``, and are granted to roles
through ``hr.Role.permissions`` by system administrators.

They deliberately carry no target-scope semantics (no own-record / department /
organization-wide meaning). Which roles hold them, and therefore who may see or
perform which payroll operation, is an administrator / business-policy
decision. The names below are provisional until that policy is confirmed; they
are isolated here so that renaming one is a one-line change.

Existing wildcard semantics are unchanged: a role holding ``payroll.*`` or
``*`` satisfies every capability below.
"""


class PayrollPermissions:
    """Capability strings for payroll operations."""

    PAYSLIP_VIEW = "payroll.payslip.view"
    PAYSLIP_PROCESS = "payroll.payslip.process"
    PAYSLIP_APPROVE = "payroll.payslip.approve"

    PROFILE_VIEW = "payroll.profile.view"
    PROFILE_MANAGE = "payroll.profile.manage"

    STATUTORY_VIEW = "payroll.statutory.view"
    STATUTORY_MANAGE = "payroll.statutory.manage"

    BANK_VIEW = "payroll.bank.view"
    BANK_MANAGE = "payroll.bank.manage"

    SUMMARY_VIEW = "payroll.summary.view"

    CONFIG_VIEW = "payroll.config.view"
    CONFIG_MANAGE = "payroll.config.manage"

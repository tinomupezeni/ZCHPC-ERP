"""
Recruitment capability identifiers (RBAC permission vocabulary).

Dotted strings matched by ``modules.identity.domain.value_objects.Permission``
and granted to roles through ``hr.Role.permissions`` by system administrators.
Which roles hold them is an administrator decision; nothing here assigns them.

The public careers surface (open job listings, anonymous application and
status lookup) is not a capability - it is available to everyone by design.
These capabilities cover the internal recruitment surface only.

Existing wildcard semantics are unchanged: ``recruitment.*`` or ``*``
satisfies every capability below.
"""


class RecruitmentPermissions:
    """Capability strings for recruitment operations."""

    JOB_VIEW = "recruitment.job.view"
    JOB_MANAGE = "recruitment.job.manage"

    APPLICATION_VIEW = "recruitment.application.view"
    APPLICATION_REVIEW = "recruitment.application.review"

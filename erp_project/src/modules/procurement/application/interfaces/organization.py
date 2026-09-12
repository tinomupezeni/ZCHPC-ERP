"""
Organizational directory port.

Business-context authorization needs to know how the actor relates to the
request's organizational unit. Procurement must not query HR tables directly,
so the relationships it depends on are expressed as a port here and adapted in
the infrastructure layer.
"""

from abc import ABC, abstractmethod


class IOrganizationalDirectory(ABC):
    """
    Read-only view of the organizational relationships that authorization needs.
    """

    @abstractmethod
    def get_department_head_id(self, department_id: int) -> int | None:
        """
        The employee recorded as responsible for the department
        (``hr.Department.head``), or None when no head is recorded.
        """
        pass

    @abstractmethod
    def get_department_id(self, employee_id: int) -> int | None:
        """Department the employee belongs to, or None if unknown/unassigned."""
        pass

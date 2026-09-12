"""
Django adapter for the organizational directory port.

Reads the organizational relationships the HR model records: which employee is
accountable for a department, and which department an employee belongs to.
"""

from modules.procurement.application.interfaces import IOrganizationalDirectory


class DjangoOrganizationalDirectory(IOrganizationalDirectory):
    """Reads organizational relationships from the HR tables."""

    def __init__(self):
        """Initialize with lazily imported models to avoid circular imports."""
        self._model = None
        self._department_model = None

    @property
    def model(self):
        """Lazy import of the Employees model."""
        if self._model is None:
            from modules.hr.infrastructure.persistence.models import Employees

            self._model = Employees
        return self._model

    @property
    def department_model(self):
        """Lazy import of the Department model."""
        if self._department_model is None:
            from modules.hr.infrastructure.persistence.models import Department

            self._department_model = Department
        return self._department_model

    def get_department_head_id(self, department_id: int) -> int | None:
        """The employee recorded as head of the department, if any."""
        return (
            self.department_model.objects.filter(pk=department_id)
            .values_list("head_id", flat=True)
            .first()
        )

    def get_department_id(self, employee_id: int) -> int | None:
        """Department the employee belongs to, or None if unknown/unassigned."""
        return (
            self.model.objects.filter(pk=employee_id)
            .values_list("department_id", flat=True)
            .first()
        )

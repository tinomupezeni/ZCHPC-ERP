"""
Django implementation of IEmployeePayrollInfoProvider.

Bridges to the HR module's Employees model plus this module's own
PayrollProfile/StatutoryProfile tables for the salary/statutory data
payroll processing needs.
"""

from typing import List


class DjangoEmployeePayrollInfoProvider:
    """Provides employee salary/statutory info for payroll processing."""

    def get_active_employee_ids(self) -> List[int]:
        """Get IDs of all active employees."""
        from modules.hr.infrastructure.persistence.models import Employees

        return list(Employees.objects.filter(is_active=True).values_list("id", flat=True))

    def get_employee_salary_info(self, employee_id: int) -> dict:
        """
        Get salary information for an employee.

        Returns dict with usd_salary, zig_salary, pays_aids_levy, employee_name.
        An employee with no PayrollProfile/StatutoryProfile yet gets zero
        salary and the statutory default (pays_aids_levy=True) rather than
        erroring - process_payroll() will just generate a zero-value payslip
        for them, which is visible and correctable, instead of the whole
        run failing on one incomplete employee record.
        """
        from modules.hr.infrastructure.persistence.models import Employees
        from modules.payroll.infrastructure.persistence.models import PayrollProfile, StatutoryProfile

        employee = Employees.objects.get(id=employee_id)

        try:
            profile = PayrollProfile.objects.get(employee_id=employee_id)
            usd_salary = profile.usd_salary
            zig_salary = profile.zig_salary
        except PayrollProfile.DoesNotExist:
            usd_salary = 0
            zig_salary = 0

        try:
            statutory = StatutoryProfile.objects.get(employee_id=employee_id)
            pays_aids_levy = statutory.pays_aids_levy
        except StatutoryProfile.DoesNotExist:
            pays_aids_levy = True

        return {
            "employee_name": f"{employee.first_name} {employee.surname}".strip(),
            "usd_salary": usd_salary,
            "zig_salary": zig_salary,
            "pays_aids_levy": pays_aids_levy,
        }

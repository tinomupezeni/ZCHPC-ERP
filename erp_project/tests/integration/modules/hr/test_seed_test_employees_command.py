"""
REM-02 follow-through: EmployeeService.create_employee now requires payroll
capabilities when the command carries salary/bank/statutory data. The
operator-run seed_test_employees command has no request actor and supplies
salary, bank and statutory data, so it passes full access explicitly. This
proves the command still seeds that data end to end.
"""

import pytest
from django.core.management import call_command

from modules.hr.infrastructure.persistence.models import Employees
from modules.payroll.infrastructure.persistence.models import (
    EmployeeBankAccount,
    PayrollProfile,
    StatutoryProfile,
)

pytestmark = pytest.mark.django_db


def test_seed_test_employees_still_creates_payroll_data():
    call_command("seed_test_employees", count=3, verbosity=0)

    seeded = Employees.objects.filter(email__startswith="testemployee")
    assert seeded.count() == 3
    for employee in seeded:
        assert PayrollProfile.objects.get(employee=employee).usd_salary > 0
        assert EmployeeBankAccount.objects.filter(employee=employee).exclude(account_number="").exists()
        assert StatutoryProfile.objects.get(employee=employee).nssa_number

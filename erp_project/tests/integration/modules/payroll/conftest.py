"""
Pytest fixtures for payroll integration tests.
"""
from decimal import Decimal

import pytest

from modules.hr.infrastructure.persistence.models import Employees
from modules.payroll.infrastructure.persistence.models import PayrollProfile


@pytest.fixture
def sample_employee(db):
    """
    One active employee on a USD 2,500 monthly salary (PY-8).

    The PayrollProfile is what makes them payable: since PY-4 a payroll run
    skips any active employee without one instead of writing a $0 payslip.
    """
    employee = Employees.objects.create(
        first_name="Farai", surname="Chuma", email="farai.chuma@zchpc.test", employee_id="EMP7001",
    )
    PayrollProfile.objects.create(employee=employee, usd_salary=Decimal("2500.00"))
    return employee

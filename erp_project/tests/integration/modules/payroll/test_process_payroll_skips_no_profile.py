"""
PY-4: an active employee with no PayrollProfile is skipped and reported,
not given a $0 payslip.

Before, DjangoEmployeePayrollInfoProvider returned a zero salary for an
employee with no profile, so every payroll run wrote $0 payslips for them.
Now the run skips them and the response lists them under
skipped_no_profile, apart from those skipped because they already have a
payslip for the period.
"""

import itertools
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.payroll.infrastructure.persistence.models import (
    DailyZiGRateToUSD,
    Payroll,
    PayrollProfile,
    TaxBracket,
)

pytestmark = pytest.mark.django_db

User = get_user_model()

PROCESS_URL = "/api/v2/payroll/payslips/"

_numbers = itertools.count(76001)


def make_employee(first, role=None):
    n = next(_numbers)
    email = f"{first.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="Pass12345!")
    return Employees.objects.create(
        user=user, first_name=first, surname="Tester", email=email, employee_id=f"EMP{n}", role=role,
    )


@pytest.fixture
def payroll_ready():
    TaxBracket.objects.create(
        currency="USD", min_income=Decimal("0"), max_income=None,
        rate=Decimal("0.20"), deduction=Decimal("0"), active_from=date(2020, 1, 1),
    )
    DailyZiGRateToUSD.objects.create(date=date.today(), average=Decimal("26"))


@pytest.fixture
def processor():
    role = Role.objects.create(
        name="PY4_PROCESSOR", display_name="Processor", permissions=["payroll.payslip.process"]
    )
    employee = make_employee("Processor", role=role)
    PayrollProfile.objects.create(employee=employee, usd_salary=Decimal("900"))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


def test_employee_without_a_payroll_profile_is_skipped_and_reported(payroll_ready, processor):
    paid = make_employee("Paid")
    PayrollProfile.objects.create(employee=paid, usd_salary=Decimal("1000"))
    unprofiled = make_employee("Unprofiled")

    response = processor.post(PROCESS_URL, {"month": "2026-08"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert Payroll.objects.filter(employee=paid).count() == 1
    assert not Payroll.objects.filter(employee=unprofiled).exists()
    reported = {e["employee_id"]: e["employee_name"] for e in response.data["skipped_no_profile"]}
    assert reported.get(unprofiled.id) == "Unprofiled Tester"
    assert paid.id not in reported
    assert response.data["total_skipped_no_profile"] == len(reported)
    assert response.data["total_errors"] == 0


def test_rerun_counts_existing_payslips_apart_from_missing_profiles(payroll_ready, processor):
    paid = make_employee("Paid")
    PayrollProfile.objects.create(employee=paid, usd_salary=Decimal("1000"))
    unprofiled = make_employee("Unprofiled")

    processor.post(PROCESS_URL, {"month": "2026-08"}, format="json")
    rerun = processor.post(PROCESS_URL, {"month": "2026-08"}, format="json")

    assert rerun.status_code == status.HTTP_201_CREATED, rerun.data
    assert rerun.data["total_processed"] == 0
    assert rerun.data["total_skipped"] >= 1  # paid (and the processor) already have one
    assert unprofiled.id in {e["employee_id"] for e in rerun.data["skipped_no_profile"]}
    assert not Payroll.objects.filter(employee=unprofiled).exists()

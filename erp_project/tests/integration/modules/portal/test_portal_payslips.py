"""
PY-1: the portal payslip endpoints returned 500 for everyone.

DjangoPayrollProvider read fields the payslip model (payroll.Payroll) does
not have: it select_related("payroll") and read payroll.period_year /
period_month, and allowances_usd / allowances_zig. The model has a single
`period` date and total_allowances_*.

Now list, detail and the yearly summary return 200 with the right figures,
and an employee still sees only their own Processed/Paid payslips.
"""

from datetime import date
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.payroll.infrastructure.persistence.models import Payroll

pytestmark = pytest.mark.django_db

User = get_user_model()

LIST_URL = "/api/v2/portal/payslips/"
SUMMARY_URL = "/api/v2/portal/payslips/summary/"

_numbers = count(75001)


def detail_url(payslip_id):
    return f"/api/v2/portal/payslips/{payslip_id}/"


def make_employee(label):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="testpass123")
    role = Role.objects.create(name=f"PAYSLIP_{n}", display_name=label, permissions=["portal.*"])
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}", role=role,
    )


def make_payslip(employee, period, status_="Processed", **amounts):
    values = dict(
        base_salary_usd=Decimal("1000.00"),
        base_salary_zig=Decimal("26000.00"),
        total_allowances_usd=Decimal("200.00"),
        total_allowances_zig=Decimal("5200.00"),
        paye_usd=Decimal("120.00"),
        total_deductions_usd=Decimal("150.00"),
        net_salary_usd=Decimal("1050.00"),
        net_salary_zig=Decimal("27300.00"),
        exchange_rate=Decimal("26.0000"),
    )
    values.update(amounts)
    return Payroll.objects.create(employee=employee, period=period, status=status_, **values)


def client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


def test_list_returns_own_processed_payslips_with_their_period():
    me, other = make_employee("Mary"), make_employee("Other")
    september = make_payslip(me, date(2026, 9, 1))
    make_payslip(me, date(2026, 8, 1), status_="Draft")
    make_payslip(other, date(2026, 9, 1))

    response = client_for(me).get(LIST_URL)

    assert response.status_code == status.HTTP_200_OK, response.data
    assert [(p["id"], p["period_year"], p["period_month"]) for p in response.data] == [
        (september.id, 2026, 9)
    ]
    assert Decimal(response.data[0]["net_salary_usd"]) == Decimal("1050.00")


def test_list_filters_by_year():
    me = make_employee("Yara")
    make_payslip(me, date(2025, 12, 1))
    make_payslip(me, date(2026, 1, 1))

    response = client_for(me).get(LIST_URL, {"year": 2025})

    assert response.status_code == status.HTTP_200_OK, response.data
    assert [(p["period_year"], p["period_month"]) for p in response.data] == [(2025, 12)]


def test_detail_shows_the_breakdown_including_allowances():
    me = make_employee("Dina")
    payslip = make_payslip(me, date(2026, 9, 1))

    response = client_for(me).get(detail_url(payslip.id))

    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["period"] == "2026-09"
    assert response.data["earnings"]["allowances"]["usd"] == "200.00"
    assert response.data["net_salary"]["usd"] == "1050.00"


def test_detail_of_someone_elses_or_a_draft_payslip_is_not_found():
    me, other = make_employee("Nia"), make_employee("Owen")
    others = make_payslip(other, date(2026, 9, 1))
    draft = make_payslip(me, date(2026, 8, 1), status_="Draft")

    assert client_for(me).get(detail_url(others.id)).status_code == status.HTTP_404_NOT_FOUND
    assert client_for(me).get(detail_url(draft.id)).status_code == status.HTTP_404_NOT_FOUND


def test_yearly_summary():
    me = make_employee("Sam")
    make_payslip(me, date(2026, 8, 1))
    make_payslip(me, date(2026, 9, 1))

    response = client_for(me).get(SUMMARY_URL, {"year": 2026})

    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["payslip_count"] == 2
    assert response.data["totals"]["net"]["usd"] == "2100.00"

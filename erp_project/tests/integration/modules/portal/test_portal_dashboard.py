"""
Portal dashboard: GET /api/v2/portal/dashboard/ returns 200 for every seeded role.

Before this fix it returned 500 "Cannot resolve keyword 'created_at'" for
every user: DashboardService called the portal leave provider, whose queries
used fields LeaveRequest/LeaveBalance do not have (created_at, days_count,
entitled_days, used_days). The portal's DashboardPage swallowed the error, so
the landing page looked empty rather than broken.

Now:
- the pending leave count comes from real LeaveRequest fields, and upcoming
  events from CompanyEvent.start_date (the events query used event_date,
  the next failure once the leave query was fixed);
- the leave balance summary is not available (null), because LeaveBalance
  holds only days_remaining and cannot give entitled/used/pending figures.

Each request carries a real JWT, so it passes through RBACMiddleware.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.management.commands.seed_evaluation import ROLE_GRANTS
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.leave.infrastructure.persistence.models import (
    CompanyEvent,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)
from modules.procurement.management.commands.seed_pr_test_data import ACTORS

pytestmark = pytest.mark.django_db

User = get_user_model()

DASHBOARD_URL = "/api/v2/portal/dashboard/"


def get_dashboard(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client.get(DASHBOARD_URL)


def seeded_employees():
    """The six seed_pr_test_data actors, the seed_admin admin, and an HR employee."""
    call_command("seed_pr_test_data")
    call_command("seed_admin")
    employees = {
        spec["role_name"]: Employees.objects.get(email=spec["email"]) for spec in ACTORS
    }
    employees["ADMIN"] = Employees.objects.get(email="admin@zchpc.ac.zw")

    hr_user = User.objects.create_user(email="hr.person@zchpc.test", password="testpass123")
    employees["HUMAN_RESOURCES"] = Employees.objects.create(
        user=hr_user,
        first_name="Hilda",
        surname="Resources",
        email="hr.person@zchpc.test",
        employee_id="EMP74001",
        role=Role.objects.get(name="HUMAN_RESOURCES"),  # migration-seeded (hr.0019)
    )
    return employees


def test_dashboard_returns_200_for_every_seeded_role():
    employees = seeded_employees()
    assert len(employees) == 8

    results = {role: get_dashboard(employee) for role, employee in employees.items()}

    failures = {
        role: (response.status_code, response.content[:200])
        for role, response in results.items()
        if response.status_code != status.HTTP_200_OK
    }
    assert failures == {}


def test_dashboard_reports_pending_leave_and_events_and_marks_balances_unavailable():
    employee = seeded_employees()["PR_TEST_REQUESTER"]
    annual = LeaveType.objects.create(name="Annual", default_days_allowed=22)
    LeaveBalance.objects.create(
        employee=employee, leave_type=annual, year=date.today().year, days_remaining=12
    )
    start = date.today() + timedelta(days=7)
    LeaveRequest.objects.create(
        employee=employee, leave_type=annual, start_date=start, end_date=start, status="Pending"
    )
    LeaveRequest.objects.create(
        employee=employee, leave_type=annual, start_date=start, end_date=start, status="Approved"
    )
    CompanyEvent.objects.create(title="Town hall", start_date=start, end_date=start)
    CompanyEvent.objects.create(
        title="Last year", start_date=date.today() - timedelta(days=365),
        end_date=date.today() - timedelta(days=365),
    )

    response = get_dashboard(employee)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["pending_leave_requests"] == 1
    assert [e["title"] for e in response.data["upcoming_events"]] == ["Town hall"]
    assert response.data["upcoming_events"][0]["event_date"] == start.isoformat()
    assert response.data["leave_balances"] is None


def test_dashboard_counts_the_reviewers_queue_separately_from_own_requests():
    """
    Staging hand check (Mon 2026-10-12): HR's dashboard showed "0 pending" while
    synergy Leave Applications listed 2. The HR, manager and admin tiles read
    pending_leave_requests, which counts the viewer's *own* pending requests.
    leave_requests_to_review is the reviewer's queue: everyone else's pending
    requests, never their own, and 0 without leave.request.review.
    """
    employees = seeded_employees()
    hr, staff = employees["HUMAN_RESOURCES"], employees["PR_TEST_REQUESTER"]
    # The migration-created role holds only hr.role.manage; staging's comes from seed_evaluation
    Role.objects.filter(pk=hr.role_id).update(permissions=ROLE_GRANTS["HUMAN_RESOURCES"])
    annual = LeaveType.objects.create(name="Annual", default_days_allowed=22)
    start = date.today() + timedelta(days=7)

    def leave(employee, status_):
        LeaveRequest.objects.create(
            employee=employee, leave_type=annual, start_date=start, end_date=start, status=status_
        )

    leave(staff, "Pending")
    leave(employees["PR_TEST_GENERAL_MANAGER"], "Pending")
    leave(staff, "Approved")
    leave(hr, "Pending")  # HR's own: not in HR's queue

    hr_data = get_dashboard(hr).data
    assert hr_data["leave_requests_to_review"] == 2
    assert hr_data["pending_leave_requests"] == 1

    staff_data = get_dashboard(staff).data
    assert staff_data["leave_requests_to_review"] == 0
    assert staff_data["pending_leave_requests"] == 1

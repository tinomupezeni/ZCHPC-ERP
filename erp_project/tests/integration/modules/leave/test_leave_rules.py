"""
Leave rules for the evaluation (PLAN §4a, confirmed in writing 2026-10-09).

1. HR cannot approve (or reject) their own leave request. The domain already
   forbade self-review; these tests pin it for the HR role the evaluation
   seeds (hr.*, leave.*, payroll.*).
2. A request over the remaining balance is refused, with a clear message:
   - at submission (already checked, now worded for a person), and
   - at approval: before, approval only failed deep in the entitlement
     ("Cannot use 5 days. Only 3 remaining.") and, with no balance row at
     all, it succeeded and deducted nothing. Now approval re-checks the
     balance first and refuses with the reason, changing nothing.
"""

import itertools
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.leave.infrastructure.persistence.models import LeaveBalance, LeaveRequest, LeaveType

pytestmark = pytest.mark.django_db

User = get_user_model()

YEAR = 2026
# Mon 5 Oct - Fri 9 Oct 2026: five days, counted either way.
START, END = date(YEAR, 10, 5), date(YEAR, 10, 9)
HR_GRANTS = ["hr.*", "leave.*", "payroll.*"]  # seed_evaluation's HUMAN_RESOURCES
STAFF_GRANTS = ["portal.*", "leave.access"]

_numbers = itertools.count(79001)


def make_employee(first, grants):
    n = next(_numbers)
    role = Role.objects.create(name=f"ROLE_{first.upper()}_{n}", permissions=list(grants))
    email = f"{first.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="Str0ng-Initial-Passw0rd")
    return Employees.objects.create(
        user=user, first_name=first, surname="Tester", email=email, employee_id=f"EMP{n}", role=role,
    )


def client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


@pytest.fixture
def annual():
    return LeaveType.objects.create(name="Annual Leave", default_days_allowed=22)


@pytest.fixture
def hr():
    return make_employee("Rutendo", HR_GRANTS)


@pytest.fixture
def staff():
    return make_employee("Tinashe", STAFF_GRANTS)


def balance(employee, leave_type, days):
    return LeaveBalance.objects.create(
        employee=employee, leave_type=leave_type, year=YEAR, days_remaining=Decimal(days)
    )


def remaining(employee, leave_type):
    return LeaveBalance.objects.get(employee=employee, leave_type=leave_type, year=YEAR).days_remaining


def pending(employee, leave_type):
    """A pending request made directly, as the seed does (no submission check)."""
    return LeaveRequest.objects.create(
        employee=employee, leave_type=leave_type, start_date=START, end_date=END,
        reason="Family visit", status="Pending",
    )


def submit(employee, leave_type):
    return client_for(employee).post(
        "/api/v2/leave/requests/",
        {"leave_type_id": leave_type.id, "start_date": START, "end_date": END, "reason": "Family visit"},
        format="json",
    )


def review(reviewer, request, approved=True):
    return client_for(reviewer).post(
        f"/api/v2/leave/requests/{request.id}/review/",
        {"approved": approved, "rejection_reason": "" if approved else "Busy period"},
        format="json",
    )


def status_of(request):
    request.refresh_from_db()
    return request.status


# =============================================================================
# 1. HR cannot review their own request
# =============================================================================


class TestHrOwnRequest:
    @pytest.mark.parametrize("approved", [True, False])
    def test_hr_cannot_review_their_own_request(self, hr, annual, approved):
        balance(hr, annual, "22")
        own = pending(hr, annual)

        response = review(hr, own, approved)

        assert response.status_code == 400
        assert response.data["error"] == (
            f"Cannot {'approve' if approved else 'reject'} request: "
            f"Cannot {'approve' if approved else 'reject'} own leave request"
        )
        assert status_of(own) == "Pending"
        assert remaining(hr, annual) == Decimal("22")

    def test_hr_approves_a_colleagues_request_and_the_balance_drops(self, hr, staff, annual):
        balance(staff, annual, "22")
        request = pending(staff, annual)

        response = review(hr, request)

        assert response.status_code == 200, response.data
        assert status_of(request) == "Approved"
        assert remaining(staff, annual) == Decimal("17")


# =============================================================================
# 2. Over the remaining balance
# =============================================================================


class TestSubmissionOverBalance:
    def test_refused_with_a_clear_message(self, staff, annual):
        balance(staff, annual, "3")

        response = submit(staff, annual)

        assert response.status_code == 400
        assert response.data["error"] == (
            "Not enough Annual Leave left: this request is for 5 days, "
            "but only 3 are available (after your other pending requests)."
        )
        assert not LeaveRequest.objects.filter(employee=staff).exists()

    def test_other_pending_requests_count_against_the_balance(self, staff, annual):
        balance(staff, annual, "7")  # 3 already pending -> 4 available, request needs 5
        LeaveRequest.objects.create(
            employee=staff, leave_type=annual, start_date=date(YEAR, 11, 2), end_date=date(YEAR, 11, 4),
            status="Pending",
        )

        response = submit(staff, annual)

        assert response.status_code == 400
        assert "only 4 are available" in response.data["error"]

    def test_no_balance_is_refused_with_a_clear_message(self, staff, annual):
        response = submit(staff, annual)

        assert response.status_code == 400
        assert response.data["error"] == (
            f"You have no Annual Leave balance for {YEAR}, so this request cannot be made. "
            "Ask HR to set up your balance."
        )

    def test_within_the_balance_is_accepted(self, staff, annual):
        balance(staff, annual, "5")
        assert submit(staff, annual).status_code == 201


class TestApprovalOverBalance:
    def test_refused_with_a_clear_message_and_nothing_changes(self, hr, staff, annual):
        balance(staff, annual, "3")
        request = pending(staff, annual)

        response = review(hr, request)

        assert response.status_code == 400
        assert response.data["error"] == (
            "Cannot approve: this request is for 5 days of Annual Leave, "
            "but the employee has only 3 left."
        )
        assert status_of(request) == "Pending"
        assert remaining(staff, annual) == Decimal("3")

    def test_balance_used_since_submission_is_caught(self, hr, staff, annual):
        balance(staff, annual, "6")
        response = submit(staff, annual)
        assert response.status_code == 201, response.data
        request = LeaveRequest.objects.get(pk=response.data["id"])
        LeaveBalance.objects.filter(employee=staff).update(days_remaining=Decimal("2"))  # e.g. an adjustment

        response = review(hr, request)

        assert response.status_code == 400
        assert "has only 2 left" in response.data["error"]
        assert status_of(request) == "Pending"

    def test_no_balance_is_refused_instead_of_approved_for_free(self, hr, staff, annual):
        request = pending(staff, annual)

        response = review(hr, request)

        assert response.status_code == 400
        assert response.data["error"] == (
            f"Cannot approve: the employee has no Annual Leave balance for {YEAR}."
        )
        assert status_of(request) == "Pending"

    def test_rejecting_needs_no_balance(self, hr, staff, annual):
        request = pending(staff, annual)
        assert review(hr, request, approved=False).status_code == 200
        assert status_of(request) == "Rejected"

    def test_exactly_the_remaining_balance_is_approved(self, hr, staff, annual):
        balance(staff, annual, "5")
        request = pending(staff, annual)

        assert review(hr, request).status_code == 200
        assert remaining(staff, annual) == Decimal("0")

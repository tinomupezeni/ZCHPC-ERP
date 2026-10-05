"""
AUD-02 Slice 1: characterization baseline for the employee/login lifecycle.

These tests record what the system does TODAY, before the F2/F3 lifecycle
remediation (Active / Deactivated / Archived). A passing test confirms the
current behaviour; it does not endorse it. Tests marked ``UNSAFE`` in their
docstring capture behaviour the remediation is expected to change - when a
later slice changes it, the matching test must be updated deliberately, in
the same commit, rather than deleted.

Every request carries a real JWT, so RBACMiddleware is on the path.

Sections:
    A. The four CustomUser.is_active x Employees.is_active combinations
    B. Deactivation and reactivation paths
    C. User deletion (refused since Slice 4)
    D. Employee (EC) identifier reuse
    E. Structural assignments (department head, reports_to, reviewers)
    F. Listing and inactive visibility
    G. Archive surface (none before Slice 6; one archive route since)
"""

from datetime import date
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.hr.infrastructure.persistence.models import (
    Department,
    EmergencyContact,
    EmployeeContact,
    Employees,
    EmploymentDetails,
    Role,
)
from modules.identity.infrastructure.persistence.models import AuditLog
from modules.leave.infrastructure.persistence.models import (
    LeaveProfile,
    LeaveRequest,
    LeaveType,
)
from modules.payroll.infrastructure.persistence.django_employee_payroll_provider import (
    DjangoEmployeePayrollInfoProvider,
)
from modules.payroll.infrastructure.persistence.models import (
    EmployeeBankAccount,
    Payroll,
    PayrollProfile,
    StatutoryProfile,
)
from modules.portal.event_handlers import _employees_with_permission
from modules.portal.infrastructure.persistence.models import Notification, SupportTicket
from modules.procurement.application.authorization import Actor
from modules.procurement.application.authorization.purchase_request_policy import (
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
USERS_URL = "/api/v2/auth/users/"
EMPLOYEES_URL = "/api/v2/hr/employees/"

REVIEW_CAPABILITY = "procurement.purchase_request.accounts_verify"
LIFECYCLE_CAPABILITIES = [
    "hr.employee.view",
    "hr.employee.create",
    "hr.employee.deactivate",
    "hr.employee.reactivate",
    "hr.employee.delete",
    "hr.employee.manage_assignments",
    "hr.department.manage",
]

# (CustomUser.is_active, Employees.is_active)
STATE_COMBINATIONS = [(True, True), (True, False), (False, True), (False, False)]

# EmployeeId accepts only EMP + digits.
_numbers = count(97001)


# =============================================================================
# Helpers
# =============================================================================


def user_url(user_id):
    return f"{USERS_URL}{user_id}/"


def employee_url(employee_id):
    return f"{EMPLOYEES_URL}{employee_id}/"


def make_employee(label, *permissions, staff=False, superuser=False, **extra):
    """A login plus employee record whose role grants exactly ``permissions``."""
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
        user = User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}",
            display_name=label,
            permissions=list(permissions),
        )
    extra.setdefault("employee_id", f"EMP{next(_numbers)}")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role, **extra
    )


def make_administrator():
    return make_employee("Lifecycleadmin", *LIFECYCLE_CAPABILITIES)


def client_for(user, raise_exceptions=True):
    client = APIClient(raise_request_exception=raise_exceptions)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def set_state(employee, *, user_active, employee_active):
    """
    Put the two flags into a combination directly, bypassing the services.

    Since Slice 2 Employees.is_active mirrors lifecycle_status (a database
    constraint), so the inactive employee state is written as DEACTIVATED.
    """
    User.objects.filter(pk=employee.user_id).update(is_active=user_active)
    Employees.objects.filter(pk=employee.pk).update(
        lifecycle_status="ACTIVE" if employee_active else "DEACTIVATED",
        is_active=employee_active,
    )


def flags(employee):
    """(CustomUser.is_active, Employees.is_active) as stored now."""
    return (
        User.objects.get(pk=employee.user_id).is_active,
        Employees.objects.get(pk=employee.pk).is_active,
    )


def listed_employee_ids(viewer, query=""):
    response = client_for(viewer.user).get(f"{EMPLOYEES_URL}{query}")
    assert response.status_code == 200, response.data
    return {row["id"] for row in response.data}


def department_head_authority(employee, department):
    """Outcome of procurement's department-head rule for this employee."""
    policy = PurchaseRequestAuthorizationPolicy(DjangoOrganizationalDirectory())
    actor = Actor(
        employee_id=employee.pk, department_id=department.pk, user_id=employee.user_id
    )

    class _Request:
        id = 1
        department_id = department.pk

    try:
        policy._require_department_authority(actor, _Request())
    except AuthorizationError as exc:
        return exc.code
    return "ALLOWED"


def give_history(employee):
    """One row in each employee-owned table that cascades on delete."""
    EmployeeContact.objects.create(employee=employee, phone="0771000000")
    EmergencyContact.objects.create(
        employee=employee, name="Kin", relationship="Sibling", phone="0772000000"
    )
    EmploymentDetails.objects.create(employee=employee)
    PayrollProfile.objects.create(employee=employee)
    StatutoryProfile.objects.create(employee=employee)
    EmployeeBankAccount.objects.create(
        employee=employee, bank_name="Bank", account_number="123", is_primary=True
    )
    LeaveProfile.objects.create(employee=employee, leave_days_entitled=22)
    AttendanceRecord.objects.create(employee=employee, date=date(2026, 9, 1))
    Notification.objects.create(
        employee=employee, title="t", message="m", notification_type="general"
    )


CASCADING_MODELS = [
    EmployeeContact,
    EmergencyContact,
    EmploymentDetails,
    PayrollProfile,
    StatutoryProfile,
    EmployeeBankAccount,
    LeaveProfile,
    AttendanceRecord,
    Notification,
]


def history_counts(employee_pk):
    return {
        model.__name__: model.objects.filter(employee_id=employee_pk).count()
        for model in CASCADING_MODELS
    }


# =============================================================================
# A. Active-state combinations
# =============================================================================


@pytest.mark.parametrize("user_active,employee_active", STATE_COMBINATIONS)
class TestActiveStateCombinations:
    """
    What each (login active, employee active) combination can do today.

    Changed by Slice 3: authentication and everything behind it now need
    BOTH the login to be enabled and the employee to be ACTIVE (one rule,
    identity.infrastructure.account_access). Before Slice 3 the main login,
    earlier tokens, refresh and role capabilities looked at the login flag
    alone, so an enabled login on an inactive employee kept full access.
    The lifecycle service no longer produces the two disagreeing
    combinations; they are still exercised here because older data may hold
    them, and they must fail closed.
    """

    def _target(self, user_active, employee_active):
        target = make_employee("Subject", "hr.employee.create", REVIEW_CAPABILITY)
        set_state(target, user_active=user_active, employee_active=employee_active)
        return target

    def test_main_login_needs_both_flags(self, user_active, employee_active):
        target = self._target(user_active, employee_active)
        response = APIClient().post(
            LOGIN_URL, {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert response.status_code == (200 if user_active and employee_active else 401)

    def test_portal_login_needs_both_flags(self, user_active, employee_active):
        target = self._target(user_active, employee_active)
        response = APIClient().post(
            PORTAL_LOGIN_URL,
            {"ec_number": target.employee_id, "password": PASSWORD},
            format="json",
        )
        assert response.status_code == (200 if user_active and employee_active else 401)

    def test_access_token_issued_earlier_needs_both_flags(self, user_active, employee_active):
        target = make_employee("Subject", "hr.employee.view")
        client = client_for(target.user)  # issued while fully active
        set_state(target, user_active=user_active, employee_active=employee_active)
        response = client.get(EMPLOYEES_URL)
        assert response.status_code == (200 if user_active and employee_active else 401)

    def test_refresh_token_issued_earlier_needs_both_flags(self, user_active, employee_active):
        target = make_employee("Subject", "hr.employee.view")
        refresh = str(RefreshToken.for_user(target.user))
        set_state(target, user_active=user_active, employee_active=employee_active)
        response = APIClient().post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert response.status_code == (200 if user_active and employee_active else 401)

    def test_role_capabilities_need_both_flags(self, user_active, employee_active):
        """The role stays attached but is dormant unless the employee is active."""
        target = self._target(user_active, employee_active)
        response = client_for(target.user).post(
            USERS_URL,
            {"email": f"made{next(_numbers)}@zchpc.test", "first_name": "M", "last_name": "A"},
            format="json",
        )
        assert response.status_code == (201 if user_active and employee_active else 401)

    def test_default_employee_listing_follows_the_employee_flag(
        self, user_active, employee_active
    ):
        target = self._target(user_active, employee_active)
        viewer = make_employee("Viewer", "hr.employee.view")
        assert (target.pk in listed_employee_ids(viewer)) is employee_active

    def test_payroll_run_membership_follows_the_employee_flag(
        self, user_active, employee_active
    ):
        """UNSAFE when (False, True): a disabled login is still paid."""
        target = self._target(user_active, employee_active)
        active_ids = DjangoEmployeePayrollInfoProvider().get_active_employee_ids()
        assert (target.pk in active_ids) is employee_active

    def test_reviewer_notification_recipients_follow_the_employee_flag(
        self, user_active, employee_active
    ):
        """UNSAFE when (False, True): work is routed to someone who cannot log in."""
        target = self._target(user_active, employee_active)
        recipients = _employees_with_permission(REVIEW_CAPABILITY)
        assert (target.pk in recipients) is employee_active


# =============================================================================
# B. Deactivation and reactivation
# =============================================================================


class TestDeactivationPaths:
    def test_hr_deactivation_disables_employee_and_login_together(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        response = client_for(admin.user).delete(
            employee_url(target.pk), {"reason": "left"}, format="json"
        )
        assert response.status_code == 200
        assert flags(target) == (False, False)

    def test_identity_deactivation_disables_employee_and_login_together(self):
        """
        Changed by Slice 3 (F2): this endpoint used to disable only the
        login, leaving the employee active (False, True). It now goes
        through the same lifecycle transition as the HR endpoint.
        """
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        response = client_for(admin.user).patch(
            user_url(target.user_id), {"is_active": False}, format="json"
        )
        assert response.status_code == 200
        assert flags(target) == (False, False)

    def test_deactivation_keeps_role_department_and_position_attached(self):
        admin = make_administrator()
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        target = make_employee("Target", "hr.employee.view", department=department)
        role_id = target.role_id
        assert client_for(admin.user).delete(employee_url(target.pk)).status_code == 200
        target.refresh_from_db()
        assert target.role_id == role_id
        assert target.department_id == department.pk

    def test_deactivation_stops_tokens_issued_earlier(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        access_client = client_for(target.user)
        refresh = str(RefreshToken.for_user(target.user))
        assert client_for(admin.user).delete(employee_url(target.pk)).status_code == 200

        assert access_client.get(EMPLOYEES_URL).status_code == 401
        refreshed = APIClient().post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert refreshed.status_code == 401

    def test_deactivation_records_no_reason_actor_or_time(self):
        """The reason is accepted and then kept nowhere in the database."""
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        audit_rows_before = AuditLog.objects.count()
        client_for(admin.user).delete(
            employee_url(target.pk), {"reason": "gross misconduct"}, format="json"
        )
        assert AuditLog.objects.count() == audit_rows_before
        stored = Employees.objects.filter(pk=target.pk).values().get()
        assert "gross misconduct" not in {str(value) for value in stored.values()}

    def test_deactivating_an_inactive_employee_succeeds_again(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(admin.user)
        assert client.delete(employee_url(target.pk)).status_code == 200
        assert client.delete(employee_url(target.pk)).status_code == 200
        assert flags(target) == (False, False)


class TestReactivationPaths:
    def _deactivated(self, admin):
        target = make_employee("Target", "hr.employee.view")
        assert client_for(admin.user).delete(employee_url(target.pk)).status_code == 200
        return target

    def test_identity_reactivation_restores_employee_and_login_together(self):
        """
        Changed by Slice 3 (F2): this endpoint used to re-enable only the
        login, leaving the employee inactive (True, False). It now goes
        through the lifecycle transition and reactivates both.
        """
        admin = make_administrator()
        target = self._deactivated(admin)
        response = client_for(admin.user).patch(
            user_url(target.user_id), {"is_active": True}, format="json"
        )
        assert response.status_code == 200
        assert flags(target) == (True, True)

    def test_reactivation_issues_a_temporary_password_and_forces_a_change(self):
        admin = make_administrator()
        target = self._deactivated(admin)
        response = client_for(admin.user).patch(
            user_url(target.user_id), {"is_active": True}, format="json"
        )
        assert response.data["temporary_password"]
        assert response.data["must_change_password"] is True
        old = APIClient().post(
            LOGIN_URL, {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert old.status_code == 401

    def test_employee_update_does_not_reactivate(self):
        """
        ``is_active`` on the employee update is accepted and ignored.
        (Since Slice 3 reactivation has its own paths: the HR reactivate
        endpoint and the identity user update.)
        """
        admin = make_administrator()
        target = self._deactivated(admin)
        response = client_for(admin.user).patch(
            employee_url(target.pk), {"is_active": True}, format="json"
        )
        assert response.status_code == 200
        assert flags(target) == (False, False)

    def test_role_is_still_attached_after_reactivation(self):
        admin = make_administrator()
        target = self._deactivated(admin)
        role_id = target.role_id
        client_for(admin.user).patch(
            user_url(target.user_id), {"is_active": True}, format="json"
        )
        target.refresh_from_db()
        assert target.role_id == role_id


# =============================================================================
# C. User deletion is refused
# =============================================================================


class TestUserDeletionIsRefused:
    """
    Changed by Slice 4 (F3). DELETE /api/v2/auth/users/<id>/ used to hard-
    delete the login, which cascaded to the employee and nine employee-owned
    tables, nulled the department head, reports_to and reviewer references,
    left no record of itself, and failed with HTTP 500 when payroll history
    protected the row. It is now refused with 405 Method Not Allowed before
    anything is read or written.
    """

    def test_delete_is_method_not_allowed(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        response = client_for(admin.user).delete(user_url(target.user_id))
        assert response.status_code == 405
        assert "DELETE" not in response["Allow"]

    def test_refused_delete_leaves_login_and_employee(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        client_for(admin.user).delete(user_url(target.user_id))
        assert User.objects.filter(pk=target.user_id).exists()
        assert Employees.objects.filter(pk=target.pk).exists()

    def test_refused_delete_leaves_every_employee_owned_record(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        give_history(target)
        client_for(admin.user).delete(user_url(target.user_id))
        assert set(history_counts(target.pk).values()) == {1}

    def test_login_audit_rows_stay_linked_to_their_user(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        AuditLog.objects.create(
            user=target.user, username_attempted=target.email, event_type="SUCCESS"
        )
        client_for(admin.user).delete(user_url(target.user_id))
        assert AuditLog.objects.get(username_attempted=target.email).user_id == target.user_id

    def test_payroll_history_no_longer_produces_a_server_error(self):
        admin = make_administrator()
        target = make_employee("Paid", "hr.employee.view")
        Payroll.objects.create(employee=target, period=date(2026, 8, 1))
        response = client_for(admin.user, raise_exceptions=False).delete(
            user_url(target.user_id)
        )
        assert response.status_code == 405
        assert Payroll.objects.filter(employee=target).exists()
        assert Employees.objects.filter(pk=target.pk).exists()

    def test_inactive_account_is_refused_too(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        set_state(target, user_active=False, employee_active=False)
        assert client_for(admin.user).delete(user_url(target.user_id)).status_code == 405
        assert Employees.objects.filter(pk=target.pk).exists()

    def test_unknown_account_gets_the_same_answer(self):
        """No existence disclosure: 405 whether or not the id exists."""
        admin = make_administrator()
        missing = "00000000-0000-0000-0000-000000000000"
        assert client_for(admin.user).delete(user_url(missing)).status_code == 405

    def test_refused_delete_is_not_a_deactivation(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        target_client = client_for(target.user)
        client_for(admin.user).delete(user_url(target.user_id))
        assert flags(target) == (True, True)
        assert target_client.get(EMPLOYEES_URL).status_code == 200

    def test_employee_endpoint_delete_is_a_deactivation_not_a_deletion(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        assert client_for(admin.user).delete(employee_url(target.pk)).status_code == 200
        assert Employees.objects.filter(pk=target.pk).exists()
        assert User.objects.filter(pk=target.user_id).exists()

    def test_email_of_an_existing_identity_cannot_be_taken_over(self):
        """Before Slice 4, deleting freed the email for a new identity."""
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(admin.user)
        client.delete(user_url(target.user_id))
        response = client.post(
            USERS_URL,
            {"email": target.email, "first_name": "Re", "last_name": "Made"},
            format="json",
        )
        assert response.status_code == 409
        assert response.data["code"] == "DUPLICATE_EMAIL"


# =============================================================================
# D. Employee identifier (EC number)
# =============================================================================


class TestEmployeeIdentifier:
    """
    The generator issues the highest existing number plus one, and the API
    accepts any client-supplied number no current row holds. Before Slice 4,
    deleting an employee removed their row, so their number could be issued
    again or claimed. Deletion is now refused, so every issued number stays
    held by its employee. (The final EC identifier policy is a later slice.)
    """

    @pytest.fixture
    def client(self):
        root = make_employee("Root", superuser=True, employee_id="EMP0001")
        return client_for(root.user)

    @staticmethod
    def _hire(client, label, **extra):
        response = client.post(
            EMPLOYEES_URL,
            {
                "first_name": label,
                "surname": "Hire",
                "email": f"{label.lower()}{next(_numbers)}@zchpc.test",
                **extra,
            },
            format="json",
        )
        assert response.status_code == 201, response.data
        return response.data

    @staticmethod
    def _attempt_delete(client, hire):
        user_id = Employees.objects.get(pk=hire["id"]).user_id
        assert client.delete(user_url(user_id)).status_code == 405

    def test_numbers_are_issued_as_highest_existing_plus_one(self, client):
        assert self._hire(client, "Alpha")["employee_id"] == "EMP0002"
        assert self._hire(client, "Bravo")["employee_id"] == "EMP0003"

    def test_number_is_not_reissued_after_a_refused_delete(self, client):
        """Changed by Slice 4: the highest number used to be reissued."""
        first = self._hire(client, "Alpha")
        self._attempt_delete(client, first)
        second = self._hire(client, "Bravo")
        assert (first["employee_id"], second["employee_id"]) == ("EMP0002", "EMP0003")

    def test_number_cannot_be_claimed_after_a_refused_delete(self, client):
        """Changed by Slice 4: a deleted number used to be claimable."""
        first = self._hire(client, "Alpha")
        self._hire(client, "Bravo")
        self._attempt_delete(client, first)
        response = client.post(
            EMPLOYEES_URL,
            {
                "first_name": "Claimant",
                "surname": "Hire",
                "email": "claimant@zchpc.test",
                "employee_id": first["employee_id"],
            },
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "DUPLICATE_EMPLOYEE_ID"

    def test_number_of_a_deactivated_employee_is_not_reissued(self, client):
        first = self._hire(client, "Alpha")
        assert client.delete(employee_url(first["id"])).status_code == 200
        assert self._hire(client, "Bravo")["employee_id"] == "EMP0003"

    def test_number_of_an_existing_employee_cannot_be_claimed(self, client):
        first = self._hire(client, "Alpha")
        response = client.post(
            EMPLOYEES_URL,
            {
                "first_name": "Dup",
                "surname": "Hire",
                "email": "dup@zchpc.test",
                "employee_id": first["employee_id"],
            },
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "DUPLICATE_EMPLOYEE_ID"

    def test_number_is_the_portal_login_identifier(self, client):
        hire = self._hire(client, "Alpha")
        assert hire["temporary_password"]
        response = APIClient().post(
            PORTAL_LOGIN_URL,
            {"ec_number": hire["employee_id"], "password": hire["temporary_password"]},
            format="json",
        )
        assert response.status_code == 200


# =============================================================================
# E. Structural assignments
# =============================================================================


class TestDepartmentHead:
    def _headed_department(self):
        head = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        return head, department

    def test_refused_delete_leaves_the_department_head(self):
        """Changed by Slice 4: deleting the head used to clear it silently."""
        admin = make_administrator()
        head, department = self._headed_department()
        assert client_for(admin.user).delete(user_url(head.user_id)).status_code == 405
        department.refresh_from_db()
        assert department.head_id == head.pk
        assert department_head_authority(head, department) == "ALLOWED"

    def test_department_without_a_head_has_no_approver(self):
        """Procurement fails closed: nobody else holds the authority."""
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        colleague = make_employee("Colleague", "hr.employee.view", department=department)
        assert department_head_authority(colleague, department) == "DEPARTMENT_HEAD_NOT_RECORDED"

    def test_deactivating_the_head_leaves_them_recorded_as_head(self):
        """UNSAFE: the department's only approver is someone who cannot log in."""
        admin = make_administrator()
        head, department = self._headed_department()
        assert client_for(admin.user).delete(employee_url(head.pk)).status_code == 200
        department.refresh_from_db()
        assert department.head_id == head.pk
        assert flags(head) == (False, False)

    def test_department_head_rule_does_not_consider_the_active_flags(self):
        admin = make_administrator()
        head, department = self._headed_department()
        client_for(admin.user).delete(employee_url(head.pk))
        assert department_head_authority(head, department) == "ALLOWED"

    def test_an_inactive_employee_can_be_appointed_head(self):
        """UNSAFE: deactivation does not exclude someone from new assignments."""
        admin = make_administrator()
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=False)
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        response = client_for(admin.user).patch(
            f"/api/v2/hr/departments/{department.pk}/", {"head_id": inactive.pk}, format="json"
        )
        assert response.status_code == 200
        department.refresh_from_db()
        assert department.head_id == inactive.pk

    def test_a_recorded_head_cannot_be_cleared_through_the_api(self):
        admin = make_administrator()
        head, department = self._headed_department()
        response = client_for(admin.user).patch(
            f"/api/v2/hr/departments/{department.pk}/", {"head_id": None}, format="json"
        )
        assert response.status_code == 200
        department.refresh_from_db()
        assert department.head_id == head.pk


class TestReportsTo:
    def test_refused_delete_leaves_reports_to(self):
        """Changed by Slice 4: deleting a manager used to null their reports' line."""
        admin = make_administrator()
        manager = make_employee("Manager", "hr.employee.view")
        report = make_employee("Report", "hr.employee.view", reports_to=manager)
        client_for(admin.user).delete(user_url(manager.user_id))
        report.refresh_from_db()
        assert report.reports_to_id == manager.pk

    def test_deactivating_a_manager_leaves_reports_to_intact(self):
        admin = make_administrator()
        manager = make_employee("Manager", "hr.employee.view")
        report = make_employee("Report", "hr.employee.view", reports_to=manager)
        client_for(admin.user).delete(employee_url(manager.pk))
        report.refresh_from_db()
        assert report.reports_to_id == manager.pk

    def test_an_inactive_employee_can_be_set_as_a_manager(self):
        admin = make_administrator()
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=False)
        report = make_employee("Report", "hr.employee.view")
        response = client_for(admin.user).patch(
            employee_url(report.pk), {"reports_to_id": inactive.pk}, format="json"
        )
        assert response.status_code == 200
        report.refresh_from_db()
        assert report.reports_to_id == inactive.pk


class TestReviewerAndAssigneeReferences:
    @staticmethod
    def _leave_request(owner, reviewer):
        leave_type = LeaveType.objects.create(name=f"Type{next(_numbers)}")
        return LeaveRequest.objects.create(
            employee=owner,
            leave_type=leave_type,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 2),
            status="Approved",
            reviewed_by=reviewer,
        )

    @staticmethod
    def _ticket(owner, assignee):
        return SupportTicket.objects.create(
            employee=owner,
            ticket_number=f"T{next(_numbers)}",
            category="IT",
            subject="s",
            description="d",
            assigned_to=assignee,
        )

    def test_refused_delete_keeps_who_approved_a_leave_request(self):
        """Changed by Slice 4: deleting the reviewer used to erase the approver."""
        admin = make_administrator()
        owner = make_employee("Owner", "hr.employee.view")
        reviewer = make_employee("Reviewer", "hr.employee.view")
        request = self._leave_request(owner, reviewer)
        client_for(admin.user).delete(user_url(reviewer.user_id))
        request.refresh_from_db()
        assert (request.status, request.reviewed_by_id) == ("Approved", reviewer.pk)

    def test_refused_delete_keeps_a_requesters_leave_requests(self):
        """Changed by Slice 4: deleting the requester used to delete their requests."""
        admin = make_administrator()
        owner = make_employee("Owner", "hr.employee.view")
        reviewer = make_employee("Reviewer", "hr.employee.view")
        request = self._leave_request(owner, reviewer)
        client_for(admin.user).delete(user_url(owner.user_id))
        assert LeaveRequest.objects.filter(pk=request.pk).exists()

    def test_refused_delete_keeps_a_ticket_assigned(self):
        """Changed by Slice 4: deleting the assignee used to unassign the ticket."""
        admin = make_administrator()
        owner = make_employee("Owner", "hr.employee.view")
        assignee = make_employee("Assignee", "hr.employee.view")
        ticket = self._ticket(owner, assignee)
        client_for(admin.user).delete(user_url(assignee.user_id))
        ticket.refresh_from_db()
        assert ticket.assigned_to_id == assignee.pk

    def test_deactivating_a_ticket_assignee_leaves_the_ticket_with_them(self):
        """UNSAFE: open work stays with someone who cannot log in."""
        admin = make_administrator()
        owner = make_employee("Owner", "hr.employee.view")
        assignee = make_employee("Assignee", "hr.employee.view")
        ticket = self._ticket(owner, assignee)
        client_for(admin.user).delete(employee_url(assignee.pk))
        ticket.refresh_from_db()
        assert ticket.assigned_to_id == assignee.pk


# =============================================================================
# F. Listing and inactive visibility
# =============================================================================


class TestEmployeeListing:
    def test_default_listing_hides_inactive_employees(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        active = make_employee("Active", "hr.employee.view")
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=False)
        listed = listed_employee_ids(viewer)
        assert active.pk in listed
        assert inactive.pk not in listed

    def test_include_inactive_needs_no_capability_beyond_reaching_hr(self):
        """UNSAFE for archival: any hr.* holder can list inactive employees."""
        viewer = make_employee("Viewer", "hr.employee.view")
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=False)
        assert inactive.pk in listed_employee_ids(viewer, "?include_inactive=true")

    def test_include_inactive_discards_the_department_filter(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        inside = make_employee("Inside", "hr.employee.view", department=department)
        outside = make_employee("Outside", "hr.employee.view")
        filtered = listed_employee_ids(viewer, f"?department_id={department.pk}")
        assert inside.pk in filtered and outside.pk not in filtered

        both = listed_employee_ids(
            viewer, f"?department_id={department.pk}&include_inactive=true"
        )
        assert outside.pk in both

    def test_inactive_employee_detail_is_still_readable(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=False)
        response = client_for(viewer.user).get(employee_url(inactive.pk))
        assert response.status_code == 200
        assert response.data["is_active"] is False


class TestUserListing:
    """
    Since AUD-02 F6 listing other logins needs hr.employee.view; is_staff
    plays no part (was: staff saw every login, everyone else only themselves).
    """

    def test_lifecycle_administrator_without_staff_lists_every_login(self):
        """Was UNSAFE-adjacent: gated on is_staff, not on a capability (F6)."""
        admin = make_administrator()
        other = make_employee("Other", "hr.employee.view")
        emails = {row["email"] for row in client_for(admin.user).get(USERS_URL).data}
        assert {admin.email, other.email} <= emails

    def test_staff_flag_without_the_capability_sees_only_themselves(self):
        staff = make_employee("Staff", "hr.employee.create", staff=True)
        make_employee("Other", "hr.employee.view")
        response = client_for(staff.user).get(USERS_URL)
        assert [row["email"] for row in response.data] == [staff.email]

    def test_listing_hides_inactive_logins_by_default(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=True)
        emails = {row["email"] for row in client_for(viewer.user).get(USERS_URL).data}
        assert inactive.email not in emails

    def test_listing_shows_inactive_logins_on_request(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        inactive = make_employee("Inactive", "hr.employee.view")
        set_state(inactive, user_active=False, employee_active=True)
        response = client_for(viewer.user).get(f"{USERS_URL}?include_inactive=true")
        assert inactive.email in {row["email"] for row in response.data}

    def test_user_listing_follows_the_login_flag_not_the_employee_flag(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        diverged = make_employee("Diverged", "hr.employee.view")
        set_state(diverged, user_active=True, employee_active=False)
        emails = {row["email"] for row in client_for(viewer.user).get(USERS_URL).data}
        assert diverged.email in emails
        assert diverged.pk not in listed_employee_ids(viewer)


# =============================================================================
# G. Archive surface
# =============================================================================


class TestNoArchiveStateExists:
    # "status" alone would match Employees.marital_status.
    LIFECYCLE_WORDS = (
        "archiv",
        "terminat",
        "lifecycle",
        "deleted",
        "offboard",
        "employment_status",
        "account_status",
    )

    @pytest.mark.parametrize(
        "model,lifecycle_fields",
        [
            # Slice 7A: the reverse relation to the lifecycle events a login
            # performed (hr.EmployeeLifecycleEvent.actor).
            (User, ["employee_lifecycle_actions"]),
            # Slice 2 introduced lifecycle_status, the only lifecycle state
            # field. Slice 7A added the event history (lifecycle_events), where
            # who/when/why live - not as fields on the employee.
            (Employees, ["lifecycle_events", "lifecycle_status"]),
        ],
    )
    def test_models_carry_no_other_lifecycle_field(self, model, lifecycle_fields):
        names = [field.name for field in model._meta.get_fields()]
        assert "is_active" in names
        assert [
            n for n in names if any(word in n for word in self.LIFECYCLE_WORDS)
        ] == lifecycle_fields

    def test_archive_is_the_only_archive_route_and_nothing_restores(self):
        """
        Changed by Slice 6: there was no archive route at all. Now there is
        exactly one (hr employee_archive), and still no route that restores,
        un-archives or terminates.
        """
        from django.urls import get_resolver

        def names(patterns):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    yield from names(pattern.url_patterns)
                elif pattern.name:
                    yield pattern.name

        route_names = set(names(get_resolver().url_patterns))
        assert [n for n in route_names if "archive" in n.lower()] == ["employee_archive"]
        assert not [
            name
            for name in route_names
            if any(word in name.lower() for word in ("restore", "unarchive", "terminate"))
        ]

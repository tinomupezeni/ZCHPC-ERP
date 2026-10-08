"""
AUD-02 Slice 4: destructive user deletion is prohibited.

User administration no longer deletes anything:

    deactivate  -> EmployeeLifecycleService (Slice 3)
    reactivate  -> EmployeeLifecycleService (Slice 3)
    delete      -> refused

DELETE /api/v2/auth/users/<id>/ has no handler, so DRF answers with its
standard 405 Method Not Allowed - the same answer the API already gives for
any method a resource does not support - and nothing is read or written.
It is deliberately not reinterpreted as a deactivation: access is ended
through the explicit lifecycle operations.

The application's delete primitives for an identity are gone too
(UserService.delete_user, the user and employee repository delete
methods), so no other caller can reach a hard delete through them.
"""

from datetime import date
from itertools import count

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.hr.application.interfaces import IEmployeeRepository
from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.application.interfaces import IUserRepository
from modules.identity.application.services import UserService
from modules.identity.infrastructure.persistence.models import AuditLog
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository
from modules.leave.infrastructure.persistence.models import LeaveProfile, LeaveRequest, LeaveType
from modules.payroll.infrastructure.persistence.models import (
    EmployeeBankAccount,
    Payroll,
    PayrollProfile,
)
from modules.portal.infrastructure.persistence.models import Notification, SupportTicket

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"

# EmployeeId accepts only EMP + digits.
_numbers = count(96001)


def user_url(user_id):
    return f"/api/v2/auth/users/{user_id}/"


def make_employee(label, *permissions, superuser=False, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
        user = User.objects.create_user(email=email, password=PASSWORD)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    extra.setdefault("employee_id", f"EMP{next(_numbers)}")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role, **extra
    )


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def a_fully_linked_employee():
    """An employee holding every kind of record Slice 1 saw deletion destroy."""
    manager = make_employee("Manager", "hr.employee.view")
    target = make_employee("Target", "hr.employee.view", reports_to=manager)
    report = make_employee("Report", "hr.employee.view", reports_to=target)
    department = Department.objects.create(name=f"Dept{next(_numbers)}", head=target)
    Employees.objects.filter(pk=target.pk).update(department=department)

    PayrollProfile.objects.create(employee=target)
    EmployeeBankAccount.objects.create(
        employee=target, bank_name="Bank", account_number="123", is_primary=True
    )
    Payroll.objects.create(employee=target, period=date(2026, 8, 1))  # PROTECT
    LeaveProfile.objects.create(employee=target, leave_days_entitled=22)
    leave_type = LeaveType.objects.create(name=f"Type{next(_numbers)}")
    LeaveRequest.objects.create(
        employee=target, leave_type=leave_type,
        start_date=date(2026, 9, 1), end_date=date(2026, 9, 2), reviewed_by=manager,
    )
    LeaveRequest.objects.create(
        employee=report, leave_type=leave_type,
        start_date=date(2026, 9, 3), end_date=date(2026, 9, 4), reviewed_by=target,
    )
    AttendanceRecord.objects.create(employee=target, date=date(2026, 9, 1))
    Notification.objects.create(employee=target, title="t", message="m", notification_type="general")
    SupportTicket.objects.create(
        employee=report, ticket_number=f"T{next(_numbers)}", category="IT",
        subject="s", description="d", assigned_to=target,
    )
    AuditLog.objects.create(user=target.user, username_attempted=target.email, event_type="SUCCESS")
    target.refresh_from_db()
    return target


def database_snapshot(target):
    """Row count of every model, plus the target's own login and employee rows."""
    counts = {model._meta.label: model.objects.count() for model in apps.get_models()}
    employee = Employees.objects.filter(pk=target.pk).values().get()
    login = User.objects.filter(pk=target.user_id).values().get()
    return counts, employee, login


# =============================================================================
# The request changes nothing
# =============================================================================


class TestDeleteRequestChangesNothing:
    def test_superuser_delete_leaves_every_table_and_both_rows_identical(self):
        root = make_employee("Root", superuser=True)
        target = a_fully_linked_employee()
        before = database_snapshot(target)

        response = client_for(root.user).delete(user_url(target.user_id))

        assert response.status_code == 405
        assert database_snapshot(target) == before

    def test_structural_references_are_untouched(self):
        root = make_employee("Root", superuser=True)
        target = a_fully_linked_employee()
        client_for(root.user).delete(user_url(target.user_id))
        assert Department.objects.get(pk=target.department_id).head_id == target.pk
        assert Employees.objects.filter(reports_to=target).exists()
        assert LeaveRequest.objects.filter(reviewed_by=target).exists()
        assert SupportTicket.objects.filter(assigned_to=target).exists()
        assert AuditLog.objects.filter(user_id=target.user_id).exists()

    def test_it_is_not_a_deactivation(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        client_for(root.user).delete(user_url(target.user_id))
        row = Employees.objects.get(pk=target.pk)
        assert (row.lifecycle_status, row.is_active) == ("ACTIVE", True)
        assert User.objects.get(pk=target.user_id).is_active is True
        login = APIClient().post(
            "/api/v2/auth/token/", {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert login.status_code == 200


# =============================================================================
# The contract
# =============================================================================


class TestDeleteContract:
    def test_answer_is_drf_method_not_allowed(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(root.user).delete(user_url(target.user_id))
        assert response.status_code == 405
        assert response.data["detail"].code == "method_not_allowed"

    def test_delete_is_not_advertised(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(root.user).options(user_url(target.user_id))
        allowed = {method.strip() for method in response["Allow"].split(",")}
        assert "DELETE" not in allowed
        assert {"GET", "PATCH"} <= allowed

    @pytest.mark.parametrize(
        "user_id", ["00000000-0000-0000-0000-000000000000", "not-a-uuid"]
    )
    def test_same_answer_for_unknown_or_malformed_ids(self, user_id):
        root = make_employee("Root", superuser=True)
        assert client_for(root.user).delete(user_url(user_id)).status_code == 405

    def test_own_account(self):
        root = make_employee("Root", superuser=True)
        assert client_for(root.user).delete(user_url(root.user_id)).status_code == 405
        assert User.objects.filter(pk=root.user_id).exists()

    def test_authentication_is_still_checked_first(self):
        target = make_employee("Target", "hr.employee.view")
        assert APIClient().delete(user_url(target.user_id)).status_code == 401

    def test_route_access_is_still_checked_first(self):
        outsider = make_employee("Outsider", "portal.view")
        target = make_employee("Target", "hr.employee.view")
        assert client_for(outsider.user).delete(user_url(target.user_id)).status_code == 403


# =============================================================================
# No application primitive can hard-delete an identity
# =============================================================================


class TestNoDeletePrimitiveRemains:
    def test_user_service_has_no_delete(self):
        assert not hasattr(UserService, "delete_user")

    @pytest.mark.parametrize(
        "repository",
        [IUserRepository, DjangoUserRepository, IEmployeeRepository, DjangoEmployeeRepository],
    )
    def test_identity_repositories_have_no_delete(self, repository):
        assert not hasattr(repository, "delete")


# =============================================================================
# The lifecycle is unaffected
# =============================================================================


class TestLifecycleStillWorks:
    def test_deactivate_and_reactivate_after_a_refused_delete(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        snapshot = Employees.objects.filter(pk=target.pk).values(
            "employee_id", "role_id", "department_id", "uuid"
        ).get()
        client = client_for(root.user)
        assert client.delete(user_url(target.user_id)).status_code == 405

        lifecycle = EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())
        lifecycle.deactivate(target.pk)
        assert Employees.objects.get(pk=target.pk).lifecycle_status == "DEACTIVATED"
        lifecycle.reactivate(target.pk)

        assert Employees.objects.get(pk=target.pk).lifecycle_status == "ACTIVE"
        assert Employees.objects.filter(pk=target.pk).values(
            "employee_id", "role_id", "department_id", "uuid"
        ).get() == snapshot

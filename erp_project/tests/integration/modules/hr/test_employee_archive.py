"""
AUD-02 Slice 6: archive - a permanently closed employment lifecycle.

    ACTIVE      -- archive -->  ARCHIVED
    DEACTIVATED -- archive -->  ARCHIVED
    ARCHIVED    -- (nothing) -->

POST /api/v2/hr/employees/<id>/archive/ needs hr.employee.archive and
authority over the target (not yourself, nobody above you). Archiving is
one transaction through EmployeeLifecycleService: the employee becomes
ARCHIVED and the login is disabled together.

Archive is not deletion: the employee row, the role, the EC number and every
historical record stay. What changes is operational:

- the identity can never authenticate again (Slice 3's rule);
- the record cannot be edited, and the employee cannot be given new
  structural assignments (department head, reports_to);
- a department head is never left in place: archiving them fails closed
  unless the request explicitly vacates the headship, and never while the
  department has purchase requests awaiting department-head approval;
- ordinary listings and lookups no longer show the employee; archived
  records need hr.employee.view_archived.
"""

from datetime import date
from itertools import count

import pytest
from django.apps import apps
from django.contrib.auth import authenticate, get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.hr.application.services import EmployeeLifecycleService, EmployeeService
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.application import services as identity_services
from modules.identity.domain.value_objects import PermissionSet
from modules.identity.infrastructure.persistence.models import AuditLog
from modules.leave.infrastructure.persistence.models import LeaveProfile, LeaveRequest, LeaveType
from modules.payroll.infrastructure.persistence.models import Payroll, PayrollProfile
from modules.procurement.application.authorization import Actor
from modules.procurement.application.authorization.purchase_request_policy import (
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from modules.procurement.infrastructure.persistence.models import PurchaseRequest
from shared.domain.exceptions import AuthorizationError, ConflictError, ValidationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"

ARCHIVIST_CAPABILITIES = [
    "hr.employee.view",
    "hr.employee.deactivate",
    "hr.employee.reactivate",
    "hr.employee.archive",
    "hr.employee.manage_assignments",
    "hr.department.manage",
]
VIEW_ARCHIVED = "hr.employee.view_archived"

_numbers = count(93001)


# =============================================================================
# Helpers
# =============================================================================


def make_employee(label, *permissions, superuser=False, staff=False, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
        user = User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    extra.setdefault("employee_id", f"EMP{next(_numbers)}")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role, **extra
    )


def archivist(*extra):
    return make_employee("Archivist", *ARCHIVIST_CAPABILITIES, *extra)


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def archive_url(employee):
    pk = employee if isinstance(employee, int) else employee.pk
    return f"{EMPLOYEES_URL}{pk}/archive/"


def archive(client, employee, **body):
    return client.post(archive_url(employee), body, format="json")


def state(employee):
    row = Employees.objects.get(pk=employee.pk)
    login = User.objects.get(pk=row.user_id).is_active if row.user_id else None
    return (row.lifecycle_status, row.is_active, login)


ARCHIVED = ("ARCHIVED", False, False)
ACTIVE = ("ACTIVE", True, True)
DEACTIVATED = ("DEACTIVATED", False, False)


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


def archived_employee(label="Archived", *permissions, **extra):
    employee = make_employee(label, *(permissions or ("hr.employee.view",)), **extra)
    lifecycle().archive(employee.pk)
    assert state(employee) == ARCHIVED
    return employee


def department_head_authority(employee, department):
    policy = PurchaseRequestAuthorizationPolicy(DjangoOrganizationalDirectory())
    actor = Actor(employee_id=employee.pk, department_id=department.pk, user_id=employee.user_id)

    class _Request:
        id = 1
        department_id = department.pk

    try:
        policy._require_department_authority(actor, _Request())
    except AuthorizationError as exc:
        return exc.code
    return "ALLOWED"


def pending_department_head_request(department, requester):
    return PurchaseRequest.objects.create(
        requisition_number=f"PR-T{next(_numbers)}",
        requester=requester,
        department=department,
        designation="Officer",
        contact="ext 1",
        status="PENDING_DEPARTMENT_HEAD",
    )


def listed_ids(viewer, query=""):
    response = client_for(viewer.user).get(f"{EMPLOYEES_URL}{query}")
    assert response.status_code == 200, response.data
    return {row["id"] for row in response.data}


# =============================================================================
# Transition contract
# =============================================================================


class TestArchiveTransition:
    def test_active_employee_is_archived_and_login_disabled(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        response = archive(client_for(actor.user), target)
        assert response.status_code == 200, response.data
        assert state(target) == ARCHIVED

    def test_deactivated_employee_is_archived(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        assert archive(client_for(actor.user), target).status_code == 200
        assert state(target) == ARCHIVED

    def test_response_reports_the_new_state(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        response = archive(client_for(actor.user), target)
        assert response.data["id"] == target.pk
        assert response.data["employee_id"] == target.employee_id
        assert response.data["lifecycle_status"] == "ARCHIVED"
        assert response.data["is_active"] is False

    def test_archiving_again_changes_nothing(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        assert archive(client, target).status_code == 200
        password = User.objects.get(pk=target.user_id).password
        assert archive(client, target).status_code == 200
        assert state(target) == ARCHIVED
        assert User.objects.get(pk=target.user_id).password == password
        assert lifecycle().archive(target.pk).changed is False

    def test_archive_repairs_a_login_left_enabled(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        Employees.objects.filter(pk=target.pk).update(lifecycle_status="DEACTIVATED", is_active=False)
        archive(client_for(actor.user), target)
        assert state(target) == ARCHIVED

    @pytest.mark.parametrize("path", ["hr_reactivate", "hr_deactivate", "identity_on", "identity_off"])
    def test_no_way_back_out(self, path):
        actor = archivist()
        target = archived_employee()
        client = client_for(actor.user)
        response = {
            "hr_reactivate": lambda: client.post(f"{EMPLOYEES_URL}{target.pk}/reactivate/"),
            "hr_deactivate": lambda: client.delete(f"{EMPLOYEES_URL}{target.pk}/"),
            "identity_on": lambda: client.patch(
                f"/api/v2/auth/users/{target.user_id}/", {"is_active": True}, format="json"
            ),
            "identity_off": lambda: client.patch(
                f"/api/v2/auth/users/{target.user_id}/", {"is_active": False}, format="json"
            ),
        }[path]()
        assert response.status_code == 400, response.data
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert state(target) == ARCHIVED

    def test_employee_without_a_login_is_archived(self):
        actor = archivist()
        target = make_employee("Nologin", "hr.employee.view")
        Employees.objects.filter(pk=target.pk).update(user=None)
        assert archive(client_for(actor.user), target).status_code == 200
        assert Employees.objects.get(pk=target.pk).lifecycle_status == "ARCHIVED"


# =============================================================================
# Authorization
# =============================================================================


class TestArchiveAuthorization:
    def test_unauthenticated_request_is_denied(self):
        target = make_employee("Target", "hr.employee.view")
        assert APIClient().post(archive_url(target)).status_code == 401
        assert state(target) == ACTIVE

    def test_lifecycle_capabilities_without_archive_are_not_enough(self):
        actor = make_employee(
            "Manager", "hr.employee.view", "hr.employee.deactivate", "hr.employee.reactivate"
        )
        target = make_employee("Target", "hr.employee.view")
        response = archive(client_for(actor.user), target)
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_ARCHIVE_NOT_AUTHORIZED"
        assert state(target) == ACTIVE

    def test_a_higher_authority_target_is_protected(self):
        actor = archivist()
        boss = make_employee("Boss", "*")
        response = archive(client_for(actor.user), boss)
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert state(boss) == ACTIVE

    def test_a_superuser_linked_employee_is_protected(self):
        actor = archivist()
        root = make_employee("Root", superuser=True)
        assert archive(client_for(actor.user), root).status_code == 403
        assert state(root) == ACTIVE

    def test_nobody_archives_themselves(self):
        actor = make_employee("Root", "*")
        response = archive(client_for(actor.user), actor)
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_SELF_ARCHIVE"
        assert state(actor) == ACTIVE

    def test_capability_is_checked_before_the_target_is_looked_up(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        actor = archivist()
        assert archive(client_for(viewer.user), 999999).status_code == 403
        assert archive(client_for(actor.user), 999999).status_code == 404

    def test_service_without_actor_permissions_fails_closed(self):
        target = make_employee("Target", "hr.employee.view")
        with pytest.raises(AuthorizationError):
            employee_service().archive_employee(target.pk)
        assert state(target) == ACTIVE


# =============================================================================
# Atomicity
# =============================================================================


class _Boom(RuntimeError):
    pass


def _raise(*args, **kwargs):
    raise _Boom("write failed")


class TestArchiveIsAtomic:
    def test_login_failure_leaves_the_employee_as_it_was(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        monkeypatch.setattr(identity_services, "disable_login", _raise)
        with pytest.raises(_Boom):
            lifecycle().archive(target.pk)
        assert state(target) == ACTIVE

    def test_failure_after_vacating_a_headship_restores_it(self, monkeypatch):
        target = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=target)
        monkeypatch.setattr(identity_services, "disable_login", _raise)
        with pytest.raises(_Boom):
            lifecycle().archive(target.pk, vacate_department_headships=True)
        assert Department.objects.get(pk=department.pk).head_id == target.pk
        assert state(target) == ACTIVE


# =============================================================================
# Authentication and runtime authorization
# =============================================================================


class TestArchivedIdentityCannotOperate:
    @pytest.fixture
    def archived(self):
        target = make_employee("Target", "hr.employee.view", "hr.employee.create")
        tokens = (client_for(target.user), str(RefreshToken.for_user(target.user)))
        lifecycle().archive(target.pk)
        return target, tokens

    def test_password_login(self, archived):
        target, _ = archived
        response = APIClient().post(
            LOGIN_URL, {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert response.status_code == 401

    def test_portal_login(self, archived):
        target, _ = archived
        response = APIClient().post(
            PORTAL_LOGIN_URL, {"ec_number": target.employee_id, "password": PASSWORD}, format="json"
        )
        assert response.status_code == 401

    def test_access_token(self, archived):
        _, (client, _) = archived
        assert client.get(EMPLOYEES_URL).status_code == 401

    def test_refresh_token(self, archived):
        _, (_, refresh) = archived
        response = APIClient().post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert response.status_code == 401

    def test_django_backend(self, archived):
        target, _ = archived
        assert authenticate(username=target.email, password=PASSWORD) is None

    def test_role_is_kept_but_cannot_be_exercised(self, archived):
        target, (client, _) = archived
        assert Employees.objects.get(pk=target.pk).role_id == target.role_id
        response = client.post(
            "/api/v2/auth/users/", {"email": "never@zchpc.test", "first_name": "N", "last_name": "E"},
            format="json",
        )
        assert response.status_code == 401
        assert not User.objects.filter(email="never@zchpc.test").exists()

    def test_login_cannot_be_switched_back_on_even_directly(self, archived):
        """A login re-enabled behind the service's back still cannot authenticate."""
        target, _ = archived
        User.objects.filter(pk=target.user_id).update(is_active=True)
        response = APIClient().post(
            LOGIN_URL, {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert response.status_code == 401


# =============================================================================
# Structural authority
# =============================================================================


class TestDepartmentHeadIsNeverLeftArchived:
    def test_archiving_a_head_fails_closed(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)

        response = archive(client_for(actor.user), head)

        assert response.status_code == 409, response.data
        assert response.data["code"] == "EMPLOYEE_ARCHIVE_BLOCKED"
        assert response.data["details"]["department_head_of"] == [department.pk]
        assert state(head) == ACTIVE
        assert Department.objects.get(pk=department.pk).head_id == head.pk

    def test_explicitly_vacating_the_headship_archives_and_leaves_it_vacant(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        colleague = make_employee("Colleague", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)

        response = archive(client_for(actor.user), head, vacate_department_headships=True)

        assert response.status_code == 200, response.data
        assert state(head) == ARCHIVED
        department.refresh_from_db()
        assert department.head_id is None
        # A vacant department has no approver at all: procurement fails closed.
        assert department_head_authority(colleague, department) == "DEPARTMENT_HEAD_NOT_RECORDED"
        assert department_head_authority(head, department) == "DEPARTMENT_HEAD_NOT_RECORDED"

    def test_pending_approvals_block_even_an_explicit_vacate(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        requester = make_employee("Requester", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        pending = pending_department_head_request(department, requester)

        response = archive(client_for(actor.user), head, vacate_department_headships=True)

        assert response.status_code == 409
        details = response.data["details"]
        assert details["department_head_of"] == [department.pk]
        assert details["pending_department_head_approvals"] == [pending.pk]
        assert state(head) == ACTIVE
        assert Department.objects.get(pk=department.pk).head_id == head.pk

    def test_reassigning_the_head_first_transfers_pending_approvals_and_unblocks(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        successor = make_employee("Successor", "hr.employee.view")
        requester = make_employee("Requester", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        pending_department_head_request(department, requester)
        client = client_for(actor.user)

        reassigned = client.patch(
            f"/api/v2/hr/departments/{department.pk}/", {"head_id": successor.pk}, format="json"
        )
        assert reassigned.status_code == 200
        assert archive(client, head).status_code == 200

        assert state(head) == ARCHIVED
        assert department_head_authority(successor, department) == "ALLOWED"

    def test_every_department_headed_is_reported(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        first = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        second = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        response = archive(client_for(actor.user), head)
        assert sorted(response.data["details"]["department_head_of"]) == sorted(
            [first.pk, second.pk]
        )

    def test_service_raises_a_conflict(self):
        head = make_employee("Head", "hr.employee.view")
        Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        with pytest.raises(ConflictError):
            lifecycle().archive(head.pk)


class TestNoNewAssignmentsToAnArchivedEmployee:
    def test_cannot_be_appointed_department_head(self):
        actor = archivist()
        archived = archived_employee()
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        response = client_for(actor.user).patch(
            f"/api/v2/hr/departments/{department.pk}/", {"head_id": archived.pk}, format="json"
        )
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert Department.objects.get(pk=department.pk).head_id is None

    def test_cannot_become_a_manager(self):
        actor = archivist()
        archived = archived_employee()
        report = make_employee("Report", "hr.employee.view")
        response = client_for(actor.user).patch(
            f"{EMPLOYEES_URL}{report.pk}/", {"reports_to_id": archived.pk}, format="json"
        )
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert Employees.objects.get(pk=report.pk).reports_to_id is None

    def test_cannot_be_named_manager_of_a_new_employee(self):
        actor = archivist("hr.employee.create")
        archived = archived_employee()
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "New", "surname": "Hire", "email": "new.hire@zchpc.test",
             "reports_to_id": archived.pk},
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert not Employees.objects.filter(email="new.hire@zchpc.test").exists()

    @pytest.mark.parametrize(
        "body", [{"first_name": "Changed"}, {"department_id": None}, {"phone": "0779999999"}]
    )
    def test_the_record_cannot_be_edited(self, body):
        actor = archivist()
        archived = archived_employee()
        before = Employees.objects.filter(pk=archived.pk).values().get()
        response = client_for(actor.user).patch(f"{EMPLOYEES_URL}{archived.pk}/", body, format="json")
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert Employees.objects.filter(pk=archived.pk).values().get() == before

    def test_the_record_cannot_be_edited_through_the_bff(self):
        root = make_employee("Root", superuser=True)
        archived = archived_employee()
        response = client_for(root.user).put(
            f"/api/v2/bff/employees/{archived.uuid}/", {"first_name": "Changed"}, format="json"
        )
        assert response.status_code == 400
        assert Employees.objects.get(pk=archived.pk).first_name == "Archived"

    def test_reports_to_pointing_at_them_is_left_in_place(self):
        """reports_to carries no runtime authority; it is kept as recorded."""
        actor = archivist()
        manager = make_employee("Manager", "hr.employee.view")
        report = make_employee("Report", "hr.employee.view", reports_to=manager)
        assert archive(client_for(actor.user), manager).status_code == 200
        assert Employees.objects.get(pk=report.pk).reports_to_id == manager.pk


# =============================================================================
# Historical integrity
# =============================================================================


class TestArchiveIsNotDeletion:
    def test_no_row_anywhere_is_removed_and_history_stays_attributed(self):
        actor = archivist()
        manager = make_employee("Manager", "hr.employee.view")
        target = make_employee("Target", "hr.employee.view", reports_to=manager)
        PayrollProfile.objects.create(employee=target)
        Payroll.objects.create(employee=target, period=date(2026, 8, 1))
        LeaveProfile.objects.create(employee=target, leave_days_entitled=22)
        leave_type = LeaveType.objects.create(name=f"Type{next(_numbers)}")
        own_leave = LeaveRequest.objects.create(
            employee=target, leave_type=leave_type,
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 2), reviewed_by=manager,
        )
        reviewed = LeaveRequest.objects.create(
            employee=manager, leave_type=leave_type, status="Approved",
            start_date=date(2026, 9, 3), end_date=date(2026, 9, 4), reviewed_by=target,
        )
        AttendanceRecord.objects.create(employee=target, date=date(2026, 9, 1))
        AuditLog.objects.create(user=target.user, username_attempted=target.email, event_type="SUCCESS")
        counts = {m._meta.label: m.objects.count() for m in apps.get_models()}
        identity = Employees.objects.filter(pk=target.pk).values(
            "id", "uuid", "employee_id", "email", "role_id", "user_id", "reports_to_id"
        ).get()

        assert archive(client_for(actor.user), target).status_code == 200

        # Nothing removed anywhere; the only new row is the archive's own
        # lifecycle event (Slice 7A).
        counts["hr.EmployeeLifecycleEvent"] += 1
        assert {m._meta.label: m.objects.count() for m in apps.get_models()} == counts
        assert Employees.objects.filter(pk=target.pk).values(
            "id", "uuid", "employee_id", "email", "role_id", "user_id", "reports_to_id"
        ).get() == identity
        assert LeaveRequest.objects.get(pk=reviewed.pk).reviewed_by_id == target.pk
        assert LeaveRequest.objects.get(pk=own_leave.pk).employee_id == target.pk
        assert AuditLog.objects.get(username_attempted=target.email).user_id == target.user_id

    def test_ec_number_stays_consumed(self):
        actor = archivist("hr.employee.create")
        target = make_employee("Target", "hr.employee.view")
        archive(client_for(actor.user), target)
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Claimant", "surname": "Hire", "email": "claimant@zchpc.test",
             "employee_id": target.employee_id},
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "DUPLICATE_EMPLOYEE_ID"


# =============================================================================
# Listings and archive-history access
# =============================================================================


class TestOperationalListingsExcludeArchived:
    def test_default_list(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        archived = archived_employee()
        assert archived.pk not in listed_ids(viewer)

    def test_include_inactive_shows_deactivated_but_not_archived(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        archived = archived_employee()
        deactivated = make_employee("Deactivated", "hr.employee.view")
        lifecycle().deactivate(deactivated.pk)
        listed = listed_ids(viewer, "?include_inactive=true")
        assert deactivated.pk in listed
        assert archived.pk not in listed

    def test_department_list(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        archived = archived_employee(department=department)
        assert archived.pk not in listed_ids(viewer, f"?department_id={department.pk}")

    def test_detail_is_not_found_without_archive_access(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        archived = archived_employee()
        assert client_for(viewer.user).get(f"{EMPLOYEES_URL}{archived.pk}/").status_code == 404

    def test_bff_detail_is_not_found_without_archive_access(self):
        viewer = make_employee("Viewer", "hr.employee.view", "bff.view")
        archived = archived_employee()
        response = client_for(viewer.user).get(f"/api/v2/bff/employees/{archived.uuid}/")
        assert response.status_code == 404

    def test_user_administration_hides_archived_logins(self):
        staff = make_employee("Staff", "hr.employee.view", staff=True)
        archived = archived_employee()
        client = client_for(staff.user)
        listed = client.get("/api/v2/auth/users/?include_inactive=true")
        assert archived.email not in {row["email"] for row in listed.data}
        assert client.get(f"/api/v2/auth/users/{archived.user_id}/").status_code == 404


class TestArchiveHistoryAccess:
    def test_asking_for_archived_records_needs_the_capability(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        archived_employee()
        response = client_for(viewer.user).get(f"{EMPLOYEES_URL}?include_archived=true")
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_VIEW_ARCHIVED_NOT_AUTHORIZED"

    def test_the_capability_lists_archived_records(self):
        historian = make_employee("Historian", "hr.employee.view", VIEW_ARCHIVED)
        archived = archived_employee()
        active = make_employee("Active", "hr.employee.view")
        listed = listed_ids(historian, "?include_archived=true")
        assert archived.pk in listed
        assert active.pk in listed

    def test_the_capability_reads_an_archived_record(self):
        historian = make_employee("Historian", "hr.employee.view", VIEW_ARCHIVED)
        archived = archived_employee()
        response = client_for(historian.user).get(f"{EMPLOYEES_URL}{archived.pk}/")
        assert response.status_code == 200
        assert response.data["employee_id"] == archived.employee_id

    def test_the_capability_reads_through_the_bff(self):
        historian = make_employee("Historian", "hr.employee.view", "bff.view", VIEW_ARCHIVED)
        # A phone number is set because of a separate, pre-existing defect:
        # any employee repository update (deactivate included) stores a
        # missing phone as "", which the BFF profile serializer rejects (500).
        archived = archived_employee(phone="0771234567")
        response = client_for(historian.user).get(f"/api/v2/bff/employees/{archived.uuid}/")
        assert response.status_code == 200

    def test_the_capability_shows_archived_logins_in_user_administration(self):
        staff = make_employee("Staff", "hr.employee.view", VIEW_ARCHIVED, staff=True)
        archived = archived_employee()
        client = client_for(staff.user)
        listed = client.get("/api/v2/auth/users/?include_inactive=true")
        assert archived.email in {row["email"] for row in listed.data}
        assert client.get(f"/api/v2/auth/users/{archived.user_id}/").status_code == 200

    def test_archive_access_does_not_grant_editing(self):
        historian = make_employee("Historian", "hr.employee.view", VIEW_ARCHIVED, "hr.employee.manage_assignments")
        archived = archived_employee()
        response = client_for(historian.user).patch(
            f"{EMPLOYEES_URL}{archived.pk}/", {"first_name": "Changed"}, format="json"
        )
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"


# =============================================================================
# Deactivated employees are not archived employees
# =============================================================================


class TestDeactivatedStaysDeactivated:
    def test_deactivation_never_archives(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        client.delete(f"{EMPLOYEES_URL}{target.pk}/")
        assert state(target) == DEACTIVATED

    def test_a_deactivated_employee_stays_visible_and_editable(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        client = client_for(actor.user)
        assert client.get(f"{EMPLOYEES_URL}{target.pk}/").status_code == 200
        response = client.patch(f"{EMPLOYEES_URL}{target.pk}/", {"phone": "0771234567"}, format="json")
        assert response.status_code == 200

    def test_a_deactivated_head_is_not_vacated_or_blocked_by_deactivation(self):
        actor = archivist()
        head = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        assert client_for(actor.user).delete(f"{EMPLOYEES_URL}{head.pk}/").status_code == 200
        assert Department.objects.get(pk=department.pk).head_id == head.pk

    def test_a_deactivated_employee_can_still_be_reactivated(self):
        actor = archivist()
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        response = client_for(actor.user).post(f"{EMPLOYEES_URL}{target.pk}/reactivate/")
        assert response.status_code == 200
        assert state(target) == ACTIVE

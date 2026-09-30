"""
AUD-02 Slice 3: atomic employee lifecycle transitions.

    ACTIVE      -- deactivate -->  DEACTIVATED
    DEACTIVATED -- reactivate -->  ACTIVE

EmployeeLifecycleService is the one place the employee's lifecycle state
and the login switch change, together and in one transaction. Both APIs that
enable or disable access go through it:

- hr:        DELETE /api/v2/hr/employees/<id>/            (deactivate)
             POST   /api/v2/hr/employees/<id>/reactivate/ (reactivate)
- identity:  PATCH  /api/v2/auth/users/<uuid>/ {"is_active": ...}

and one rule (identity.infrastructure.account_access) keeps a login whose
employee is not ACTIVE from authenticating or operating.

There is no transition into or out of ARCHIVED in this slice.
"""

from datetime import date
from itertools import count

import pytest
from django.contrib.auth import authenticate, get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.hr.application.services import EmployeeLifecycleService, EmployeeService
from modules.hr.domain.events import EmployeeTerminatedEvent
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.application import services as identity_services
from modules.identity.application.services import UpdateUserCommand, UserService
from modules.identity.domain.value_objects import PermissionSet
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository
from modules.leave.infrastructure.persistence.models import LeaveRequest, LeaveType
from modules.payroll.infrastructure.persistence.models import PayrollProfile
from shared.domain.exceptions import NotFoundError, ValidationError
from shared.infrastructure import EventBus

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
EMPLOYEES_URL = "/api/v2/hr/employees/"

LIFECYCLE_CAPABILITIES = [
    "hr.employee.view",
    "hr.employee.deactivate",
    "hr.employee.reactivate",
]

ACTIVE = ("ACTIVE", True, True)
DEACTIVATED = ("DEACTIVATED", False, False)

# EmployeeId accepts only EMP + digits.
_numbers = count(99001)


# =============================================================================
# Helpers
# =============================================================================


def make_employee(label, *permissions, superuser=False, login=True, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    user = None
    if login and superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    elif login:
        user = User.objects.create_user(email=email, password=PASSWORD)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    extra.setdefault("employee_id", f"EMP{next(_numbers)}")
    employee = Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role, **extra
    )
    if user is None:
        # The post_save signal provisions a login for an employee with an
        # email; remove it to model an employee without one.
        Employees.objects.filter(pk=employee.pk).update(user=None)
        employee.refresh_from_db()
    return employee


def make_administrator():
    return make_employee("Lifecycleadmin", *LIFECYCLE_CAPABILITIES)


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def state(employee):
    """(lifecycle_status, Employees.is_active, CustomUser.is_active) as stored."""
    row = Employees.objects.get(pk=employee.pk)
    login_active = User.objects.get(pk=row.user_id).is_active if row.user_id else None
    return (row.lifecycle_status, row.is_active, login_active)


def store(employee, status, *, login_active):
    """Write a combination straight to the rows, bypassing the service."""
    Employees.objects.filter(pk=employee.pk).update(
        lifecycle_status=status, is_active=status == "ACTIVE"
    )
    User.objects.filter(pk=employee.user_id).update(is_active=login_active)
    employee.refresh_from_db()
    return employee


def hr_deactivate(client, employee, reason="left"):
    return client.delete(f"{EMPLOYEES_URL}{employee.pk}/", {"reason": reason}, format="json")


def hr_reactivate(client, employee):
    return client.post(f"{EMPLOYEES_URL}{employee.pk}/reactivate/")


def identity_set_active(client, employee, active):
    return client.patch(
        f"/api/v2/auth/users/{employee.user_id}/", {"is_active": active}, format="json"
    )


DEACTIVATE_PATHS = {
    "hr": hr_deactivate,
    "identity": lambda client, employee: identity_set_active(client, employee, False),
}
REACTIVATE_PATHS = {
    "hr": hr_reactivate,
    "identity": lambda client, employee: identity_set_active(client, employee, True),
}


def main_login(email, password=PASSWORD):
    return APIClient().post(LOGIN_URL, {"email": email, "password": password}, format="json")


def portal_login(ec_number, password=PASSWORD):
    return APIClient().post(
        PORTAL_LOGIN_URL, {"ec_number": ec_number, "password": password}, format="json"
    )


def lifecycle_service():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


@pytest.fixture
def terminated_events():
    """EmployeeTerminatedEvents published during the test."""
    seen = []
    bus = EventBus.get_instance()
    bus.subscribe(EmployeeTerminatedEvent, seen.append)
    yield seen
    bus.unsubscribe(EmployeeTerminatedEvent, seen.append)


# =============================================================================
# Deactivation: ACTIVE -> DEACTIVATED
# =============================================================================


@pytest.mark.parametrize("path", DEACTIVATE_PATHS)
class TestDeactivation:
    """Both endpoints perform the same transition."""

    def test_employee_state_mirror_and_login_change_together(self, path):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        assert state(target) == ACTIVE

        response = DEACTIVATE_PATHS[path](client_for(admin.user), target)

        assert response.status_code == 200
        assert state(target) == DEACTIVATED

    def test_identity_and_assignments_are_untouched(self, path):
        admin = make_administrator()
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        manager = make_employee("Manager", "hr.employee.view")
        target = make_employee(
            "Target", "hr.employee.view", department=department, reports_to=manager
        )
        report = make_employee("Report", "hr.employee.view", reports_to=target)
        Department.objects.filter(pk=department.pk).update(head=target)
        PayrollProfile.objects.create(employee=target)
        leave = LeaveRequest.objects.create(
            employee=target,
            leave_type=LeaveType.objects.create(name=f"Type{next(_numbers)}"),
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 2),
            reviewed_by=manager,
        )
        before = Employees.objects.filter(pk=target.pk).values(
            "employee_id", "role_id", "department_id", "reports_to_id", "user_id", "email"
        ).get()

        DEACTIVATE_PATHS[path](client_for(admin.user), target)

        after = Employees.objects.filter(pk=target.pk).values(
            "employee_id", "role_id", "department_id", "reports_to_id", "user_id", "email"
        ).get()
        assert after == before
        assert Department.objects.get(pk=department.pk).head_id == target.pk
        assert Employees.objects.get(pk=report.pk).reports_to_id == target.pk
        assert PayrollProfile.objects.filter(employee_id=target.pk).exists()
        assert LeaveRequest.objects.get(pk=leave.pk).reviewed_by_id == manager.pk

    def test_a_new_login_is_refused_everywhere(self, path):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        DEACTIVATE_PATHS[path](client_for(admin.user), target)

        assert main_login(target.email).status_code == 401
        assert portal_login(target.employee_id).status_code == 401
        assert authenticate(username=target.email, password=PASSWORD) is None

    def test_an_access_token_issued_earlier_stops_working(self, path):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(target.user)
        assert client.get(EMPLOYEES_URL).status_code == 200

        DEACTIVATE_PATHS[path](client_for(admin.user), target)

        assert client.get(EMPLOYEES_URL).status_code == 401

    def test_a_refresh_token_issued_earlier_cannot_mint_access(self, path):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        refresh = str(RefreshToken.for_user(target.user))

        DEACTIVATE_PATHS[path](client_for(admin.user), target)

        response = APIClient().post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert response.status_code == 401
        assert "access" not in response.data

    def test_the_role_stays_attached_but_cannot_be_exercised(self, path):
        # The actor must hold what the target holds to deactivate them.
        admin = make_employee("Admin", *LIFECYCLE_CAPABILITIES, "hr.employee.create")
        target = make_employee("Target", "hr.employee.view", "hr.employee.create")
        role_id = target.role_id
        client = client_for(target.user)

        response = DEACTIVATE_PATHS[path](client_for(admin.user), target)

        assert response.status_code == 200
        assert Employees.objects.get(pk=target.pk).role_id == role_id
        response = client.post(
            "/api/v2/auth/users/",
            {"email": "never@zchpc.test", "first_name": "N", "last_name": "E"},
            format="json",
        )
        assert response.status_code == 401
        assert not User.objects.filter(email="never@zchpc.test").exists()


class TestDeactivationDetails:
    def test_employee_without_a_login_is_deactivated(self):
        admin = make_administrator()
        target = make_employee("Nologin", "hr.employee.view", login=False)
        assert hr_deactivate(client_for(admin.user), target).status_code == 200
        assert state(target) == ("DEACTIVATED", False, None)

    def test_the_existing_event_is_published_once_with_the_reason(self, terminated_events):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        hr_deactivate(client_for(admin.user), target, reason="suspended pending review")
        assert [(e.employee_id, e.reason) for e in terminated_events] == [
            (target.pk, "suspended pending review")
        ]

    def test_a_login_with_no_employee_record_only_has_its_switch_changed(self):
        """e.g. a bootstrap account: there is no employment lifecycle to move."""
        root = make_employee("Root", superuser=True)
        bare = User.objects.create_user(email="bare.login@zchpc.test", password=PASSWORD)
        client = client_for(root.user)

        off = client.patch(f"/api/v2/auth/users/{bare.pk}/", {"is_active": False}, format="json")
        assert off.status_code == 200
        assert User.objects.get(pk=bare.pk).is_active is False

        on = client.patch(f"/api/v2/auth/users/{bare.pk}/", {"is_active": True}, format="json")
        assert on.status_code == 200
        assert on.data["temporary_password"]
        assert User.objects.get(pk=bare.pk).is_active is True


# =============================================================================
# Reactivation: DEACTIVATED -> ACTIVE
# =============================================================================


@pytest.mark.parametrize("path", REACTIVATE_PATHS)
class TestReactivation:
    def _deactivated(self, **extra):
        target = make_employee("Target", "hr.employee.view", **extra)
        lifecycle_service().deactivate(target.pk)
        assert state(target) == DEACTIVATED
        return target

    def test_employee_state_mirror_and_login_change_together(self, path):
        admin = make_administrator()
        target = self._deactivated()

        response = REACTIVATE_PATHS[path](client_for(admin.user), target)

        assert response.status_code == 200
        assert state(target) == ACTIVE

    def test_it_is_the_same_employee_with_the_same_assignments(self, path):
        admin = make_administrator()
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        target = self._deactivated(department=department)
        fields = ("id", "uuid", "employee_id", "role_id", "department_id", "user_id", "email")
        before = Employees.objects.filter(pk=target.pk).values(*fields).get()
        employees_before = Employees.objects.count()

        REACTIVATE_PATHS[path](client_for(admin.user), target)

        assert Employees.objects.filter(pk=target.pk).values(*fields).get() == before
        assert Employees.objects.count() == employees_before

    def test_a_temporary_password_is_issued_and_must_be_changed(self, path):
        """REM-07's contract, unchanged: the old password is never restored."""
        admin = make_administrator()
        target = self._deactivated()

        response = REACTIVATE_PATHS[path](client_for(admin.user), target)

        temporary_password = response.data["temporary_password"]
        assert temporary_password and temporary_password != PASSWORD
        assert User.objects.get(pk=target.user_id).must_change_password is True
        assert main_login(target.email).status_code == 401
        login = main_login(target.email, temporary_password)
        assert login.status_code == 200
        assert login.data["user"]["must_change_password"] is True

    def test_the_employee_can_sign_in_to_the_portal_again(self, path):
        admin = make_administrator()
        target = self._deactivated()
        response = REACTIVATE_PATHS[path](client_for(admin.user), target)
        portal = portal_login(target.employee_id, response.data["temporary_password"])
        assert portal.status_code == 200

    def test_tokens_from_before_the_deactivation_stay_dead(self, path):
        """The password changed, so they are revoked for good (CHECK_REVOKE_TOKEN)."""
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        old_client = client_for(target.user)
        old_refresh = str(RefreshToken.for_user(target.user))
        lifecycle_service().deactivate(target.pk)

        REACTIVATE_PATHS[path](client_for(admin.user), target)

        assert old_client.get(EMPLOYEES_URL).status_code == 401
        refreshed = APIClient().post(REFRESH_URL, {"refresh": old_refresh}, format="json")
        assert refreshed.status_code == 200
        stale = APIClient()
        stale.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}")
        assert stale.get(EMPLOYEES_URL).status_code == 401


class TestHrReactivationEndpoint:
    def test_response_reports_the_new_state(self):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        response = hr_reactivate(client_for(admin.user), target)
        assert response.data["id"] == target.pk
        assert response.data["employee_id"] == target.employee_id
        assert response.data["lifecycle_status"] == "ACTIVE"
        assert response.data["is_active"] is True

    def test_employee_without_a_login_is_reactivated_with_no_password(self):
        admin = make_administrator()
        target = make_employee("Nologin", "hr.employee.view", login=False)
        lifecycle_service().deactivate(target.pk)
        response = hr_reactivate(client_for(admin.user), target)
        assert response.status_code == 200
        assert response.data["temporary_password"] is None
        assert state(target) == ("ACTIVE", True, None)

    def test_unauthenticated_request_is_denied(self):
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        assert hr_reactivate(APIClient(), target).status_code == 401
        assert state(target) == DEACTIVATED

    def test_actor_without_the_capability_is_denied(self):
        actor = make_employee("Viewer", "hr.employee.view", "hr.employee.deactivate")
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        response = hr_reactivate(client_for(actor.user), target)
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_REACTIVATE_NOT_AUTHORIZED"
        assert state(target) == DEACTIVATED

    def test_a_dormant_role_still_counts_as_the_targets_authority(self):
        """A deactivated administrator cannot be brought back by a lesser actor."""
        admin = make_administrator()
        privileged = make_employee("Boss", "*")
        lifecycle_service().deactivate(privileged.pk)
        response = hr_reactivate(client_for(admin.user), privileged)
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert state(privileged) == DEACTIVATED

    def test_capability_is_checked_before_the_target_is_looked_up(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        admin = make_administrator()
        missing = f"{EMPLOYEES_URL}999999/reactivate/"
        assert client_for(viewer.user).post(missing).status_code == 403
        assert client_for(admin.user).post(missing).status_code == 404

    def test_service_without_actor_permissions_fails_closed(self):
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        from shared.domain.exceptions import AuthorizationError

        with pytest.raises(AuthorizationError):
            employee_service().reactivate_employee(target.pk)
        assert state(target) == DEACTIVATED


# =============================================================================
# Transitions that are not allowed, or change nothing
# =============================================================================


class TestArchivedIsOutsideTheseTransitions:
    """There is no way into or out of ARCHIVED here."""

    @pytest.fixture
    def archived(self):
        target = make_employee("Archived", "hr.employee.view")
        return store(target, "ARCHIVED", login_active=False)

    def test_hr_deactivate_is_refused(self, archived):
        response = hr_deactivate(client_for(make_administrator().user), archived)
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert state(archived) == ("ARCHIVED", False, False)

    def test_hr_reactivate_is_refused(self, archived):
        response = hr_reactivate(client_for(make_administrator().user), archived)
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert state(archived) == ("ARCHIVED", False, False)

    @pytest.mark.parametrize("active", [True, False])
    def test_identity_update_is_refused(self, archived, active):
        response = identity_set_active(client_for(make_administrator().user), archived, active)
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert state(archived) == ("ARCHIVED", False, False)

    def test_refusal_does_not_touch_a_login_that_was_left_enabled(self, archived):
        """Nothing is half-applied; and that login still cannot be used."""
        store(archived, "ARCHIVED", login_active=True)
        with pytest.raises(ValidationError):
            lifecycle_service().reactivate(archived.pk)
        with pytest.raises(ValidationError):
            lifecycle_service().deactivate(archived.pk)
        assert state(archived) == ("ARCHIVED", False, True)
        assert main_login(archived.email).status_code == 401

    def test_no_transition_produces_archived(self):
        target = make_employee("Target", "hr.employee.view")
        service = lifecycle_service()
        assert not hasattr(service, "archive")
        service.deactivate(target.pk)
        service.reactivate(target.pk)
        assert state(target)[0] == "ACTIVE"


class TestRequestingTheCurrentState:
    """Asking for the state already held succeeds and changes nothing."""

    def test_deactivating_a_deactivated_employee(self, terminated_events):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(admin.user)
        assert hr_deactivate(client, target).status_code == 200
        updated_before = User.objects.get(pk=target.user_id).password

        assert hr_deactivate(client, target).status_code == 200

        assert state(target) == DEACTIVATED
        assert User.objects.get(pk=target.user_id).password == updated_before
        assert len(terminated_events) == 1  # no second event

    def test_service_reports_that_nothing_changed(self):
        target = make_employee("Target", "hr.employee.view")
        service = lifecycle_service()
        assert service.deactivate(target.pk).changed is True
        assert service.deactivate(target.pk).changed is False
        assert service.reactivate(target.pk).changed is True
        again = service.reactivate(target.pk)
        assert (again.changed, again.temporary_password) == (False, None)

    @pytest.mark.parametrize("path", REACTIVATE_PATHS)
    def test_reactivating_an_active_employee_issues_no_password(self, path):
        admin = make_administrator()
        target = make_employee("Target", "hr.employee.view")
        target_client = client_for(target.user)

        response = REACTIVATE_PATHS[path](client_for(admin.user), target)

        assert response.status_code == 200
        assert response.data.get("temporary_password") is None
        assert state(target) == ACTIVE
        assert User.objects.get(pk=target.user_id).must_change_password is False
        assert main_login(target.email).status_code == 200  # password untouched
        assert target_client.get(EMPLOYEES_URL).status_code == 200  # token still valid

    def test_missing_employee_is_not_found(self):
        with pytest.raises(NotFoundError):
            lifecycle_service().deactivate(999999)
        with pytest.raises(NotFoundError):
            lifecycle_service().reactivate(999999)


class TestTransitionsRepairADisagreement:
    """
    Rows written before Slice 3 (or by something that bypassed the service)
    may disagree. A transition always leaves both sides in the target state.
    """

    def test_deactivating_disables_a_login_left_enabled(self):
        admin = make_administrator()
        target = store(make_employee("Target", "hr.employee.view"), "DEACTIVATED", login_active=True)
        assert hr_deactivate(client_for(admin.user), target).status_code == 200
        assert state(target) == DEACTIVATED

    def test_deactivating_moves_an_employee_whose_login_was_already_disabled(self):
        admin = make_administrator()
        target = store(make_employee("Target", "hr.employee.view"), "ACTIVE", login_active=False)
        assert hr_deactivate(client_for(admin.user), target).status_code == 200
        assert state(target) == DEACTIVATED

    def test_reactivating_enables_a_login_left_disabled(self):
        admin = make_administrator()
        target = store(make_employee("Target", "hr.employee.view"), "ACTIVE", login_active=False)
        response = hr_reactivate(client_for(admin.user), target)
        assert response.status_code == 200
        assert response.data["temporary_password"]
        assert state(target) == ACTIVE

    def test_reactivating_moves_an_employee_whose_login_was_left_enabled(self):
        admin = make_administrator()
        target = store(make_employee("Target", "hr.employee.view"), "DEACTIVATED", login_active=True)
        response = hr_reactivate(client_for(admin.user), target)
        assert response.status_code == 200
        assert response.data["temporary_password"] is None  # that login was never disabled
        assert state(target) == ACTIVE


# =============================================================================
# Atomicity: a failure on either side leaves both as they were
# =============================================================================


class _Boom(RuntimeError):
    pass


def _raise(*args, **kwargs):
    raise _Boom("write failed")


class TestTransitionsAreAtomic:
    def test_deactivation_login_failure_rolls_back_the_employee(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        monkeypatch.setattr(identity_services, "disable_login", _raise)
        with pytest.raises(_Boom):
            lifecycle_service().deactivate(target.pk)
        assert state(target) == ACTIVE

    def test_deactivation_employee_failure_leaves_the_login(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        monkeypatch.setattr(DjangoEmployeeRepository, "update", _raise)
        with pytest.raises(_Boom):
            lifecycle_service().deactivate(target.pk)
        assert state(target) == ACTIVE

    def test_reactivation_login_failure_rolls_back_the_employee(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        monkeypatch.setattr(identity_services, "enable_login", _raise)
        with pytest.raises(_Boom):
            lifecycle_service().reactivate(target.pk)
        assert state(target) == DEACTIVATED

    def test_reactivation_failure_after_the_password_was_issued_keeps_the_old_one(
        self, monkeypatch
    ):
        """The login write itself is inside the transaction too."""
        target = make_employee("Target", "hr.employee.view")
        lifecycle_service().deactivate(target.pk)
        password_before = User.objects.get(pk=target.user_id).password
        real_enable = identity_services.enable_login

        def enable_then_fail(user_repository, user_id):
            real_enable(user_repository, user_id)
            raise _Boom("failed after the login was written")

        monkeypatch.setattr(identity_services, "enable_login", enable_then_fail)
        with pytest.raises(_Boom):
            lifecycle_service().reactivate(target.pk)

        assert state(target) == DEACTIVATED
        user = User.objects.get(pk=target.user_id)
        assert user.password == password_before
        assert user.must_change_password is False

    @pytest.mark.parametrize("active", [False, True])
    def test_identity_path_is_atomic_with_the_rest_of_the_update(self, monkeypatch, active):
        """A rename in the same request fails after the transition: both undo."""
        target = make_employee("Target", "hr.employee.view")
        if active:
            lifecycle_service().deactivate(target.pk)
        before = state(target)
        service = UserService(DjangoUserRepository())
        real_get = service._get
        calls = []

        def get_then_fail(user_id):
            calls.append(user_id)
            if len(calls) > 1:  # the reload after the transition
                raise _Boom("failed after the transition")
            return real_get(user_id)

        monkeypatch.setattr(service, "_get", get_then_fail)
        with pytest.raises(_Boom):
            service.update_user(
                UpdateUserCommand(user_id=target.user_id, is_active=active, first_name="New"),
                actor_permissions=PermissionSet.full_access(),
            )
        assert state(target) == before

    def test_hr_service_path_is_atomic(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        monkeypatch.setattr(identity_services, "disable_login", _raise)
        with pytest.raises(_Boom):
            employee_service().deactivate_employee(
                target.pk, actor_permissions=PermissionSet.full_access()
            )
        assert state(target) == ACTIVE


# =============================================================================
# Runtime enforcement of a disagreement the service did not create
# =============================================================================


@pytest.mark.parametrize("status", ["DEACTIVATED", "ARCHIVED"])
class TestNonActiveEmployeeCannotOperateEvenWithAnEnabledLogin:
    """One rule, asked at every way in (identity.infrastructure.account_access)."""

    def _target(self, status, **kwargs):
        target = make_employee("Target", "hr.employee.view", **kwargs)
        tokens = (client_for(target.user), str(RefreshToken.for_user(target.user)))
        store(target, status, login_active=True)
        return target, tokens

    def test_main_login(self, status):
        target, _ = self._target(status)
        assert main_login(target.email).status_code == 401

    def test_portal_login(self, status):
        target, _ = self._target(status)
        assert portal_login(target.employee_id).status_code == 401

    def test_access_token(self, status):
        target, (client, _) = self._target(status)
        response = client.get(EMPLOYEES_URL)
        assert response.status_code == 401

    def test_refresh_token(self, status):
        target, (_, refresh) = self._target(status)
        response = APIClient().post(REFRESH_URL, {"refresh": refresh}, format="json")
        assert response.status_code == 401

    def test_personal_routes_are_not_an_exception(self, status):
        target, (client, _) = self._target(status)
        assert client.get("/api/v2/auth/users/me/").status_code == 401

    def test_superuser_flag_is_not_an_exception(self, status):
        target, (client, _) = self._target(status, superuser=True)
        assert client.get(EMPLOYEES_URL).status_code == 401
        assert main_login(target.email).status_code == 401

    def test_django_backend_login(self, status):
        target, _ = self._target(status)
        assert authenticate(username=target.email, password=PASSWORD) is None

    def test_existing_django_session(self, status):
        """A session opened earlier stops resolving to the user (EmailBackend)."""
        from django.test import Client

        target, _ = self._target(status)
        client = Client()
        client.force_login(target.user)
        response = client.get(EMPLOYEES_URL)
        assert response.status_code == 401
        assert "_auth_user_id" in client.session  # the session exists; the user does not load


class TestEnforcementDoesNotAffectOthers:
    def test_active_employee_is_unaffected(self):
        target = make_employee("Target", "hr.employee.view")
        assert main_login(target.email).status_code == 200
        assert client_for(target.user).get(EMPLOYEES_URL).status_code == 200

    def test_login_without_an_employee_record_is_unaffected(self):
        root = User.objects.create_superuser(email="bare.root@zchpc.test", password=PASSWORD)
        assert main_login(root.email).status_code == 200
        assert client_for(root).get(EMPLOYEES_URL).status_code == 200

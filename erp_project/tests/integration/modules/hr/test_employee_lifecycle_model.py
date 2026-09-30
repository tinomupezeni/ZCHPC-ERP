"""
AUD-02 Slice 2: the employee lifecycle model.

Employees.lifecycle_status (ACTIVE / DEACTIVATED / ARCHIVED) is the one
authoritative statement of employment state. Employees.is_active remains as
a stored compatibility mirror that the database forces to agree with it.

This slice establishes the model only. Tests marked ``NOT YET ENFORCED``
record where the state is not applied yet (authentication, authorization,
transitions into ARCHIVED); later slices are expected to change them.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.domain.value_objects import EmployeeLifecycleStatus
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.payroll.infrastructure.persistence.django_employee_payroll_provider import (
    DjangoEmployeePayrollInfoProvider,
)
from modules.payroll.infrastructure.persistence.models import PayrollProfile

User = get_user_model()
Status = EmployeeLifecycleStatus

PASSWORD = "EmployeePass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
LOGIN_URL = "/api/v2/auth/token/"

# EmployeeId accepts only EMP + digits.
_numbers = count(98001)


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


def store_state(employee, status):
    """Write a lifecycle state (and its mirror) straight to the row."""
    Employees.objects.filter(pk=employee.pk).update(
        lifecycle_status=status.value, is_active=status is Status.ACTIVE
    )
    employee.refresh_from_db()
    return employee


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def stored(employee):
    return Employees.objects.values_list("lifecycle_status", "is_active").get(pk=employee.pk)


# =============================================================================
# Representation
# =============================================================================


@pytest.mark.django_db
class TestLifecycleStateIsRepresented:
    def test_a_new_row_is_active_by_default(self):
        employee = make_employee("Fresh")
        assert stored(employee) == ("ACTIVE", True)

    @pytest.mark.parametrize("status", list(Status))
    def test_each_state_can_be_stored_and_read_back(self, status):
        employee = store_state(make_employee("Subject"), status)
        entity = DjangoEmployeeRepository().get_by_id(employee.pk)
        assert entity.lifecycle_status is status
        assert entity.is_active is (status is Status.ACTIVE)
        assert entity.is_archived is (status is Status.ARCHIVED)

    def test_model_choices_are_exactly_the_domain_states(self):
        field = Employees._meta.get_field("lifecycle_status")
        assert [value for value, _ in field.choices] == [status.value for status in Status]

    def test_repository_persists_the_state_with_its_mirror(self):
        employee = make_employee("Subject")
        repository = DjangoEmployeeRepository()
        entity = repository.get_by_id(employee.pk)
        entity.deactivate()
        repository.update(entity)
        assert stored(employee) == ("DEACTIVATED", False)


# =============================================================================
# Integrity
# =============================================================================


@pytest.mark.django_db
class TestLifecycleIntegrity:
    @staticmethod
    def _rejected(employee, **values):
        with pytest.raises(IntegrityError), transaction.atomic():
            Employees.objects.filter(pk=employee.pk).update(**values)

    @pytest.mark.parametrize("value", ["DELETED", "INACTIVE", "active", ""])
    def test_database_rejects_an_unknown_state(self, value):
        employee = make_employee("Subject")
        self._rejected(employee, lifecycle_status=value, is_active=False)
        assert stored(employee) == ("ACTIVE", True)

    def test_database_rejects_a_missing_state(self):
        employee = make_employee("Subject")
        self._rejected(employee, lifecycle_status=None, is_active=False)

    def test_model_validation_rejects_an_unknown_state(self):
        employee = make_employee("Subject")
        employee.lifecycle_status = "DELETED"
        with pytest.raises(DjangoValidationError) as exc:
            employee.full_clean()
        assert "lifecycle_status" in exc.value.message_dict

    def test_is_active_cannot_be_cleared_while_the_state_is_active(self):
        """The old way of deactivating - writing the flag alone - is refused."""
        employee = make_employee("Subject")
        self._rejected(employee, is_active=False)

    @pytest.mark.parametrize("status", [Status.DEACTIVATED, Status.ARCHIVED])
    def test_is_active_cannot_stay_set_in_a_non_active_state(self, status):
        employee = make_employee("Subject")
        self._rejected(employee, lifecycle_status=status.value)

    @pytest.mark.parametrize("status", [Status.DEACTIVATED, Status.ARCHIVED])
    def test_is_active_cannot_be_set_in_a_non_active_state(self, status):
        employee = store_state(make_employee("Subject"), status)
        self._rejected(employee, is_active=True)
        assert stored(employee) == (status.value, False)


# =============================================================================
# Compatibility with the existing paths and is_active readers
# =============================================================================


@pytest.mark.django_db
class TestExistingPathsWriteTheLifecycleState:
    def test_employee_created_through_the_api_is_active(self):
        root = make_employee("Root", superuser=True)
        response = client_for(root.user).post(
            EMPLOYEES_URL,
            {"first_name": "New", "surname": "Hire", "email": "new.hire@zchpc.test"},
            format="json",
        )
        assert response.status_code == 201, response.data
        assert stored(Employees.objects.get(pk=response.data["id"])) == ("ACTIVE", True)

    def test_hr_deactivation_moves_the_employee_to_deactivated(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        assert client_for(root.user).delete(f"{EMPLOYEES_URL}{target.pk}/").status_code == 200
        assert stored(target) == ("DEACTIVATED", False)

    def test_deactivation_keeps_role_and_department(self):
        root = make_employee("Root", superuser=True)
        department = Department.objects.create(name=f"Dept{next(_numbers)}")
        target = make_employee("Target", "hr.employee.view", department=department)
        role_id = target.role_id
        client_for(root.user).delete(f"{EMPLOYEES_URL}{target.pk}/")
        target.refresh_from_db()
        assert (target.role_id, target.department_id) == (role_id, department.pk)

    def test_an_archived_employee_is_not_turned_back_into_a_deactivated_one(self):
        root = make_employee("Root", superuser=True)
        target = store_state(make_employee("Target", "hr.employee.view"), Status.ARCHIVED)
        response = client_for(root.user).delete(f"{EMPLOYEES_URL}{target.pk}/")
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert stored(target) == ("ARCHIVED", False)


@pytest.mark.django_db
class TestIsActiveReadersFollowTheLifecycleState:
    """Code that still filters on is_active sees only ACTIVE employees."""

    @pytest.mark.parametrize("status", list(Status))
    def test_default_employee_listing(self, status):
        viewer = make_employee("Viewer", "hr.employee.view")
        subject = store_state(make_employee("Subject"), status)
        listed = {row["id"] for row in client_for(viewer.user).get(EMPLOYEES_URL).data}
        assert (subject.pk in listed) is (status is Status.ACTIVE)

    @pytest.mark.parametrize("status", list(Status))
    def test_payroll_run_membership(self, status):
        subject = store_state(make_employee("Subject"), status)
        active_ids = DjangoEmployeePayrollInfoProvider().get_active_employee_ids()
        assert (subject.pk in active_ids) is (status is Status.ACTIVE)


@pytest.mark.django_db
class TestLifecycleStateIsNotYetEnforced:
    """What Slice 2 deliberately leaves for later slices."""

    def test_identity_deactivation_does_not_touch_the_lifecycle_state(self):
        """NOT YET ENFORCED (F2): the login is disabled, the employee stays ACTIVE."""
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(root.user).patch(
            f"/api/v2/auth/users/{target.user_id}/", {"is_active": False}, format="json"
        )
        assert response.status_code == 200
        assert stored(target) == ("ACTIVE", True)
        assert User.objects.get(pk=target.user_id).is_active is False

    @pytest.mark.parametrize("status", [Status.DEACTIVATED, Status.ARCHIVED])
    def test_login_is_not_blocked_by_the_lifecycle_state(self, status):
        """NOT YET ENFORCED: authentication still reads only CustomUser.is_active."""
        target = store_state(make_employee("Target", "hr.employee.view"), status)
        response = APIClient().post(
            LOGIN_URL, {"email": target.email, "password": PASSWORD}, format="json"
        )
        assert response.status_code == 200

    def test_no_api_moves_an_employee_to_archived(self):
        """NOT YET ENFORCED: lifecycle_status is not accepted by the update API."""
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(root.user).patch(
            f"{EMPLOYEES_URL}{target.pk}/", {"lifecycle_status": "ARCHIVED"}, format="json"
        )
        assert response.status_code == 200
        assert stored(target) == ("ACTIVE", True)


# =============================================================================
# Migration of existing employees
# =============================================================================

BEFORE = [("hr", "0020_seed_employee_lifecycle_permissions")]


@pytest.mark.django_db(transaction=True)
class TestExistingEmployeesAreClassified:
    """Runs hr 0021/0022 for real against rows created on the 0020 schema."""

    @pytest.fixture
    def before_lifecycle(self):
        executor = MigrationExecutor(connection)
        executor.migrate(BEFORE)
        try:
            yield executor.loader.project_state(BEFORE).apps
        finally:
            self._migrate_to_latest()

    @staticmethod
    def _migrate_to_latest():
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_existing_rows_are_classified_and_nothing_else_changes(self, before_lifecycle):
        OldEmployees = before_lifecycle.get_model("hr", "Employees")
        OldRole = before_lifecycle.get_model("hr", "Role")
        OldDepartment = before_lifecycle.get_model("hr", "Department")
        assert "lifecycle_status" not in [f.name for f in OldEmployees._meta.get_fields()]

        role = OldRole.objects.create(name="MIGRATED_ROLE", permissions=["hr.employee.view"])
        department = OldDepartment.objects.create(name="Migrated Department")

        def old_employee(number, *, employee_active, user_active=None, **extra):
            # Logins come from the current model: the identity app is not
            # rolled back, only hr is.
            user_id = None
            if user_active is not None:
                user_id = User.objects.create_user(
                    email=f"migrated{number}@zchpc.test",
                    password=PASSWORD,
                    is_active=user_active,
                ).pk
            return OldEmployees.objects.create(
                employee_id=f"EMP9{number:04d}",
                first_name="Migrated",
                surname=str(number),
                email=f"migrated{number}@zchpc.test",
                is_active=employee_active,
                user_id=user_id,
                **extra,
            )

        active = old_employee(1, employee_active=True, user_active=True)
        inactive = old_employee(
            2, employee_active=False, user_active=False, role=role, department=department
        )
        active_with_disabled_login = old_employee(3, employee_active=True, user_active=False)
        inactive_with_live_login = old_employee(4, employee_active=False, user_active=True)
        without_login = old_employee(5, employee_active=False, reports_to=inactive)
        OldDepartment.objects.filter(pk=department.pk).update(head=inactive)
        PayrollProfile.objects.create(employee_id=inactive.pk)
        total_before = OldEmployees.objects.count()

        self._migrate_to_latest()

        assert Employees.objects.count() == total_before
        assert stored(active) == ("ACTIVE", True)
        assert stored(inactive) == ("DEACTIVATED", False)
        # Only the employee flag decides; the login's flag is left as it was.
        assert stored(active_with_disabled_login) == ("ACTIVE", True)
        assert stored(inactive_with_live_login) == ("DEACTIVATED", False)
        assert stored(without_login) == ("DEACTIVATED", False)
        assert not Employees.objects.filter(lifecycle_status="ARCHIVED").exists()
        assert User.objects.get(pk=active_with_disabled_login.user_id).is_active is False
        assert User.objects.get(pk=inactive_with_live_login.user_id).is_active is True

        migrated = Employees.objects.get(pk=inactive.pk)
        assert migrated.role_id == role.pk
        assert migrated.department_id == department.pk
        assert migrated.user_id == inactive.user_id
        assert Department.objects.get(pk=department.pk).head_id == inactive.pk
        assert Employees.objects.get(pk=without_login.pk).reports_to_id == inactive.pk
        assert PayrollProfile.objects.filter(employee_id=inactive.pk).exists()

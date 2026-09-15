"""
Integration tests for the seed_pr_test_data management command.

Why a command and not (only) the pytest fixtures: see the module docstring
of modules.procurement.management.commands.seed_pr_test_data - this command
persists the same six actors conftest.py's make_employee fixture defines,
outside of pytest's rolled-back transaction, so they survive between manual
requests against a running dev server. These tests verify the command
itself, using the application's real permission system (PermissionSet), not
role-name string matching - the same standard the command's own
verification step holds itself to.
"""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

import pytest

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from modules.procurement.management.commands.seed_pr_test_data import (
    ACTORS,
    TEST_PASSWORD,
)

pytestmark = pytest.mark.django_db

User = get_user_model()

EXPECTED_EMAILS = {spec["key"]: spec["email"] for spec in ACTORS}


def _employee(key: str) -> Employees:
    return Employees.objects.select_related("user", "role", "department").get(
        email=EXPECTED_EMAILS[key]
    )


class TestFirstRunCreatesAllSixActors:
    def test_all_six_employees_exist_with_the_expected_names_and_emails(self):
        call_command("seed_pr_test_data")

        for spec in ACTORS:
            employee = Employees.objects.get(email=spec["email"])
            assert employee.first_name == spec["first_name"]
            assert employee.surname == spec["surname"]
            assert employee.is_active is True

    def test_each_employee_has_a_real_generated_ec_number(self):
        call_command("seed_pr_test_data")

        ec_numbers = set()
        for spec in ACTORS:
            employee = Employees.objects.get(email=spec["email"])
            assert employee.employee_id
            assert employee.employee_id.startswith("EMP")
            ec_numbers.add(employee.employee_id)

        # Six distinct actors must not collide on the same EC number.
        assert len(ec_numbers) == 6

    def test_each_employee_has_a_linked_user_whose_password_is_testpass123(self):
        call_command("seed_pr_test_data")

        for spec in ACTORS:
            employee = _employee(spec["key"])
            assert employee.user is not None
            assert employee.user.check_password(TEST_PASSWORD)

    def test_no_test_actor_is_an_admin_or_superuser(self):
        call_command("seed_pr_test_data")

        for spec in ACTORS:
            employee = _employee(spec["key"])
            assert employee.user.is_superuser is False
            assert employee.user.is_staff is False


class TestRolesAndPermissions:
    """
    Checks actual permission-matching via PermissionSet (the same object
    Actor.has_permission uses in production), not role name comparisons.
    """

    def _permissions_of(self, key: str) -> PermissionSet:
        employee = _employee(key)
        return PermissionSet.from_list(list(employee.role.permissions))

    def test_requester_can_create_view_submit_correct_and_resubmit(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("requester")

        for permission in (P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT):
            assert perms.has_permission(permission)

    def test_department_head_can_view_approve_and_reject(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("department_head")

        for permission in (P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT):
            assert perms.has_permission(permission)

    def test_accounts_can_view_verify_and_reject(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("accounts")

        for permission in (P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT):
            assert perms.has_permission(permission)

    def test_general_manager_can_view_recommend_and_reject(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("general_manager")

        for permission in (P.GM_RECOMMEND, P.VIEW, P.REJECT):
            assert perms.has_permission(permission)

    def test_director_can_view_approve_and_reject(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("director")

        for permission in (P.DIRECTOR_APPROVE, P.VIEW, P.REJECT):
            assert perms.has_permission(permission)

    def test_procurement_can_view_and_process(self):
        call_command("seed_pr_test_data")
        perms = self._permissions_of("procurement")

        for permission in (P.PROCESS, P.VIEW):
            assert perms.has_permission(permission)

    def test_no_actor_holds_a_permission_outside_their_own_stage(self):
        """
        Riley (requester-only) must not, for example, be able to approve at
        the department-head stage - each dedicated role carries exactly its
        own stage's capabilities (see the command's module docstring on why
        roles aren't shared/reused).
        """
        call_command("seed_pr_test_data")

        assert not self._permissions_of("requester").has_permission(P.DEPARTMENT_HEAD_APPROVE)
        assert not self._permissions_of("accounts").has_permission(P.GM_RECOMMEND)
        assert not self._permissions_of("procurement").has_permission(P.DIRECTOR_APPROVE)


class TestDepartmentHeadRelationship:
    def test_hana_is_assigned_as_it_department_head(self):
        call_command("seed_pr_test_data")

        hana = _employee("department_head")
        department = Department.objects.get(pk=hana.department_id)

        assert department.head_id == hana.id

    def test_riley_and_hana_share_the_same_department(self):
        call_command("seed_pr_test_data")

        riley = _employee("requester")
        hana = _employee("department_head")

        assert riley.department_id is not None
        assert riley.department_id == hana.department_id

    def test_reuses_an_existing_it_department_rather_than_creating_a_duplicate(self):
        existing = Department.objects.create(name="IT Department", description="Pre-existing")

        call_command("seed_pr_test_data")

        hana = _employee("department_head")
        assert hana.department_id == existing.id
        assert Department.objects.filter(name__iexact="IT Department").count() == 1

    def test_reuses_the_bare_it_department_naming_convention_too(self):
        existing = Department.objects.create(name="IT", description="Pre-existing (seed_admin convention)")

        call_command("seed_pr_test_data")

        hana = _employee("department_head")
        assert hana.department_id == existing.id


class TestIdempotency:
    def test_running_twice_creates_no_duplicate_employees_or_users(self):
        call_command("seed_pr_test_data")
        call_command("seed_pr_test_data")

        for spec in ACTORS:
            assert Employees.objects.filter(email=spec["email"]).count() == 1
            assert User.objects.filter(email=spec["email"]).count() == 1

    def test_running_twice_keeps_the_same_ec_numbers(self):
        call_command("seed_pr_test_data")
        first_ec_numbers = {
            spec["key"]: _employee(spec["key"]).employee_id for spec in ACTORS
        }

        call_command("seed_pr_test_data")
        second_ec_numbers = {
            spec["key"]: _employee(spec["key"]).employee_id for spec in ACTORS
        }

        assert first_ec_numbers == second_ec_numbers

    def test_running_twice_keeps_hana_as_department_head(self):
        call_command("seed_pr_test_data")
        call_command("seed_pr_test_data")

        hana = _employee("department_head")
        department = Department.objects.get(pk=hana.department_id)
        assert department.head_id == hana.id

    def test_reconciles_a_password_changed_out_of_band(self):
        call_command("seed_pr_test_data")
        riley = _employee("requester")
        riley.user.set_password("something-else")
        riley.user.save()

        call_command("seed_pr_test_data")

        riley.user.refresh_from_db()
        assert riley.user.check_password(TEST_PASSWORD)


class TestDryRun:
    def test_dry_run_saves_nothing(self):
        call_command("seed_pr_test_data", dry_run=True)

        assert Employees.objects.count() == 0
        assert Role.objects.filter(name__startswith="PR_TEST_").count() == 0


class TestFailsSafelyOnConflict:
    def test_a_conflicting_non_test_employee_at_one_of_the_emails_blocks_the_whole_run(self):
        Employees.objects.create(
            first_name="Someone",
            surname="Else",
            email="riley.requester@example.com",
        )

        with pytest.raises(CommandError):
            call_command("seed_pr_test_data")

    def test_transactional_no_partial_data_is_left_behind_on_failure(self):
        """
        The conflict is on the *last*-processed actor (Procurement), so by
        the time it's detected, roles/employees for the other five would
        already have been created if this weren't wrapped in one atomic
        transaction. Confirms it actually is.
        """
        Employees.objects.create(
            first_name="Someone",
            surname="Else",
            email="pat.procure@example.com",
        )

        with pytest.raises(CommandError):
            call_command("seed_pr_test_data")

        # Only the pre-existing conflicting row remains - nothing from this
        # command's other five actors was left behind.
        assert Employees.objects.count() == 1
        assert Role.objects.filter(name__startswith="PR_TEST_").count() == 0
        assert Department.objects.filter(name__iexact="IT Department").count() == 0
        assert Department.objects.filter(name__iexact="IT").count() == 0

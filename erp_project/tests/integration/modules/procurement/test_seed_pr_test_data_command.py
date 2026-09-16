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
from modules.identity.infrastructure.route_access import grants_module_access
from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from modules.procurement.management.commands.seed_pr_test_data import (
    ACTORS,
    PORTAL_NOTIFICATION_PERMISSION,
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


class TestDepartmentHeadPortalNotificationAccess:
    """
    F19 follow-up: Hana must be able to reach GET /api/v2/portal/notifications/
    to see and follow the "Purchase Request Corrected" notification - which
    the coarse RBAC gate (grants_module_access) denies unless her role holds
    at least one portal.*-prefixed permission. These tests exercise that
    actual gate function, not just permission-string presence, and confirm
    the grant is scoped to Hana alone.
    """

    def test_department_head_role_has_the_portal_notification_permission(self):
        call_command("seed_pr_test_data")

        perms = PermissionSet.from_list(
            list(_employee("department_head").role.permissions)
        )
        assert perms.has_permission(PORTAL_NOTIFICATION_PERMISSION)

    def test_department_head_can_pass_the_real_rbac_module_gate_for_portal_routes(self):
        """
        The actual function RBACMiddleware calls to decide route access -
        not a re-derived assertion about permission strings.
        """
        call_command("seed_pr_test_data")

        perms = PermissionSet.from_list(
            list(_employee("department_head").role.permissions)
        )
        assert grants_module_access(perms, "portal") is True

    def test_department_head_still_passes_the_procurement_gate_too(self):
        """Adding the portal permission must not come at the cost of the existing procurement access."""
        call_command("seed_pr_test_data")

        perms = PermissionSet.from_list(
            list(_employee("department_head").role.permissions)
        )
        assert grants_module_access(perms, "procurement") is True

    def test_no_other_seeded_actor_receives_the_portal_notification_permission(self):
        """
        Only Hana's own workflow required this - granting it to the other
        five would be exactly the "broad/unrelated" over-grant the task
        explicitly ruled out.
        """
        call_command("seed_pr_test_data")

        for key in ("requester", "accounts", "general_manager", "director", "procurement"):
            perms = PermissionSet.from_list(list(_employee(key).role.permissions))
            assert not perms.has_permission(PORTAL_NOTIFICATION_PERMISSION)
            assert grants_module_access(perms, "portal") is False


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


class TestDepartmentHeadReceivesTheCorrectedNotificationThroughTheRealApi:
    """
    F19 follow-up: end-to-end proof that the permission fix actually unblocks
    the real workflow, not just that the right permission string is present -
    drives login, submit, approve, reject, correct-and-resubmit, and the
    notification list entirely through real HTTP against the seeded accounts,
    the same sequence the manual QA in this follow-up's own report performs
    by hand.
    """

    def _login(self, ec_number):
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.post(
            "/api/v2/portal/auth/login/",
            {"ec_number": ec_number, "password": TEST_PASSWORD},
            format="json",
        )
        assert response.status_code == 200, response.data
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    def test_hana_can_retrieve_the_corrected_notification_after_the_real_workflow(self):
        call_command("seed_pr_test_data")
        riley = _employee("requester")
        hana = _employee("department_head")
        adam = _employee("accounts")

        from modules.accounts.infrastructure.persistence.models import AccountChart

        budget_code = AccountChart.objects.filter(account_type="regular").first()
        if budget_code is None:
            budget_code = AccountChart.objects.create(
                code="TEST-1", name="Test Account", account_type="regular"
            )

        riley_client = self._login(riley.employee_id)
        created = riley_client.post(
            "/api/v2/procurement/requests/",
            {
                "items": [
                    {
                        "description": "Laptop",
                        "quantity": 1,
                        "expected_delivery_period": "2 weeks",
                        "estimated_cost": "500.00",
                        "budget_code_id": budget_code.id,
                    }
                ]
            },
            format="json",
        )
        assert created.status_code == 201, created.data
        request_id = created.data["id"]
        submitted = riley_client.post(f"/api/v2/procurement/requests/{request_id}/submit/")
        assert submitted.status_code == 200, submitted.data

        hana_client = self._login(hana.employee_id)
        approved = hana_client.post(
            f"/api/v2/procurement/requests/{request_id}/department-head/approve/"
        )
        assert approved.status_code == 200, approved.data

        # The request is now PENDING_ACCOUNTS - rejecting it requires the
        # Accounts stage's own authority (accounts_verify), not the
        # Department Head's, so it's Adam (not Hana) who rejects here. This
        # mirrors the F19 business walkthrough: a later-stage rejection still
        # sends the corrected-and-resubmitted request back through
        # PENDING_DEPARTMENT_HEAD, so Hana is the one who must be notified.
        adam_client = self._login(adam.employee_id)
        rejected = adam_client.post(
            f"/api/v2/procurement/requests/{request_id}/reject/",
            {"reason": "Please pick a different model"},
            format="json",
        )
        assert rejected.status_code == 200, rejected.data

        corrected = riley_client.post(
            f"/api/v2/procurement/requests/{request_id}/correct-and-resubmit/"
        )
        assert corrected.status_code == 200, corrected.data
        resubmitted = riley_client.post(f"/api/v2/procurement/requests/{request_id}/submit/")
        assert resubmitted.status_code == 200, resubmitted.data
        assert resubmitted.data["status"] == "PENDING_DEPARTMENT_HEAD"

        # Before the fix, this call itself returned 403 - proving the
        # permission gap is what blocked the notification UI, not the
        # notification's own creation (which was always correct).
        notifications = hana_client.get("/api/v2/portal/notifications/")
        assert notifications.status_code == 200, notifications.data

        matches = [
            n
            for n in notifications.data
            if n["notification_type"] == "purchase_request_corrected"
            and n["related_object_id"] == request_id
        ]
        assert len(matches) == 1
        notification = matches[0]
        assert notification["title"] == "Purchase Request Corrected"
        assert "has been corrected and requires your re-approval" in notification["message"]
        assert notification["is_read"] is False


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

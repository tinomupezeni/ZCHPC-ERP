"""
Regression guard for the reconciled RBAC route gate.

This file previously asserted the opposite: that RBACMiddleware refused a
department head holding every Slice 4 capability, because it authorized routes
from a hard-coded role-name map that never consulted hr.Role.permissions.

That conflict is resolved - the middleware now derives coarse route access from
the same authoritative permission store - so these tests pin the fix in place
using realistic organizational role names.
"""

from decimal import Decimal
from importlib import import_module

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.hr.infrastructure.persistence.models import (
    Department,
    Employees,
    Position,
    Role,
)
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestCategory,
    PurchaseRequestItem,
)

pytestmark = pytest.mark.django_db

REQUESTS_URL = "/api/v2/procurement/requests/"
User = get_user_model()


def employee_client(email, role_name, permissions, department, employee_code):
    """An authenticated client for an employee with a realistic role name."""
    role = Role.objects.create(
        name=role_name,
        display_name=role_name.replace("_", " ").title(),
        permissions=list(permissions),
    )
    user = User.objects.create_user(email=email, password="BlockerPass123!")
    employee = Employees.objects.create(
        user=user,
        first_name="Test",
        surname=role_name.title(),
        email=f"{employee_code}@zchpc.test",
        department=department,
        role=role,
        employee_id=employee_code,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client, employee


class TestDepartmentManagerReachesTheApi:
    """
    DEPARTMENT_MANAGER is the role the legacy map rejected outright. It must
    now reach the API on the strength of its granted permission alone.
    """

    def test_department_manager_can_approve_through_the_full_stack(self):
        it = Department.objects.create(name="IT Department")
        budget_code = AccountChart.objects.create(
            code="3001", name="Hardware", account_type="regular"
        )

        _, requester = employee_client(
            "staff@zchpc.test", "REGULAR_STAFF", [P.CREATE, P.VIEW], it, "EMP7001"
        )
        head_client, head = employee_client(
            "manager@zchpc.test",
            "DEPARTMENT_MANAGER",
            [P.DEPARTMENT_HEAD_APPROVE],
            it,
            "EMP7002",
        )
        it.head = head
        it.save(update_fields=["head"])

        record = PurchaseRequestModel.objects.create(
            requester=requester,
            department=it,
            designation="Developer",
            contact="ext 1",
            status="PENDING_DEPARTMENT_HEAD",
            total_estimated_cost=Decimal("500.00"),
        )
        PurchaseRequestItem.objects.create(
            purchase_request=record,
            description="Monitor",
            quantity=1,
            expected_delivery_period="1 week",
            estimated_cost=Decimal("500.00"),
            category=PurchaseRequestCategory.objects.create(
                name="Hardware", account_chart=budget_code
            ),
            budget_code=budget_code,
        )

        response = head_client.post(
            f"{REQUESTS_URL}{record.id}/department-head/approve/"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        record.refresh_from_db()
        assert record.status == "PENDING_ACCOUNTS"
        assert record.decisions.get().actor_id == head.id

    def test_a_role_with_no_procurement_permission_is_still_refused(self):
        """The gate did not simply open for everyone."""
        it = Department.objects.create(name="IT Department")
        client, _ = employee_client(
            "hronly@zchpc.test", "HUMAN_RESOURCES", ["hr.*"], it, "EMP7003"
        )

        response = client.get(REQUESTS_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        # The route gate answers with a bare JsonResponse detail, whereas the
        # application answers with an error code - so this was refused at the
        # gate, which is exactly what should still happen here.
        assert "code" not in response.json()


# =============================================================================
# F09-PR: coverage proving the *migration* grants these permissions
# =============================================================================
#
# Migration module names start with a digit, so they cannot be imported with
# ordinary import syntax - the same reason
# tests/integration/modules/identity/test_role_permission_seeding.py uses
# importlib for 0017.
_seed_migration = import_module(
    "modules.hr.migrations.0018_seed_purchase_request_permissions"
)
PURCHASE_REQUEST_ROLE_PERMISSIONS = _seed_migration.PURCHASE_REQUEST_ROLE_PERMISSIONS
grant_purchase_request_permissions = _seed_migration.grant_purchase_request_permissions


class _HistoricalApps:
    """Minimal stand-in for the migration's historical model registry."""

    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("hr", "Role")
        return Role


def run_purchase_request_permission_seeding():
    """
    Apply 0018's RunPython forwards function directly.

    Nothing in the normal pytest-django database lifecycle creates
    REGULAR_STAFF/DEPARTMENT_MANAGER/ACCOUNTANT/etc. rows before a test does,
    so the migration itself is a no-op when it actually runs while the test
    database is built. Calling its forwards function directly - against a
    role a test creates first, exactly as it would already exist in a real
    deployment - is how tests/integration/modules/identity
    /test_role_permission_seeding.py exercises 0017's own RunPython function,
    and is the only way to prove this migration's logic (rather than a
    permission list a test fixture typed in) is what grants access.
    """
    grant_purchase_request_permissions(_HistoricalApps(), None)


class TestPurchaseRequestPermissionSeedingMigration:
    """
    Pins the seeding migration's own behavior in isolation: additive merging,
    idempotency, name-matching, and that it never touches a role outside its
    six target roles. TestMigratedPermissionsReachTheLiveApi and
    TestEmployeeDepartmentHeadAccountsChainViaMigratedPermissions below prove
    the same grants actually reach the live API.
    """

    @pytest.mark.parametrize("role_name", list(PURCHASE_REQUEST_ROLE_PERMISSIONS))
    def test_target_role_receives_exactly_its_mapped_grant(self, role_name):
        role = Role.objects.create(name=role_name, permissions=[])

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        assert role.permissions == PURCHASE_REQUEST_ROLE_PERMISSIONS[role_name]

    def test_role_name_spelling_variants_are_matched(self):
        """The migration's own normalisation (copied from 0017's) is exercised."""
        role = Role.objects.create(name="department-manager", permissions=[])

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        assert (
            role.permissions
            == PURCHASE_REQUEST_ROLE_PERMISSIONS["DEPARTMENT_MANAGER"]
        )

    def test_unrelated_permissions_are_preserved_and_extended(self):
        """Case B: a role with unrelated permissions keeps them and gains the PR grant."""
        role = Role.objects.create(
            name="ACCOUNTANT", permissions=["payroll.*", "accounts.*"]
        )

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        assert role.permissions == [
            "payroll.*",
            "accounts.*",
            *PURCHASE_REQUEST_ROLE_PERMISSIONS["ACCOUNTANT"],
        ]

    def test_partially_granted_role_is_topped_up_without_duplication(self):
        """Case C: PR permissions already present are not duplicated."""
        role = Role.objects.create(
            name="PROCUREMENT_OFFICER", permissions=[P.CREATE, P.VIEW]
        )

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        expected = [
            P.CREATE,
            P.VIEW,
            *[
                permission
                for permission in PURCHASE_REQUEST_ROLE_PERMISSIONS[
                    "PROCUREMENT_OFFICER"
                ]
                if permission not in (P.CREATE, P.VIEW)
            ],
        ]
        assert role.permissions == expected
        assert len(role.permissions) == len(set(role.permissions))

    def test_seeding_is_idempotent(self):
        role = Role.objects.create(name="REGULAR_STAFF", permissions=[])

        run_purchase_request_permission_seeding()
        first = list(Role.objects.get(pk=role.pk).permissions)
        run_purchase_request_permission_seeding()

        assert Role.objects.get(pk=role.pk).permissions == first

    def test_role_outside_this_slices_target_list_is_left_untouched(self):
        """Case D: not one of the six target roles - nothing granted or invented."""
        role = Role.objects.create(name="SALES_REPRESENTATIVE", permissions=[])

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        assert role.permissions == []

    def test_human_resources_gets_only_its_mapped_requester_grant(self):
        """
        HR must not receive approval authority merely because the role
        exists - only exactly what DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS
        assigns it.
        """
        role = Role.objects.create(name="HUMAN_RESOURCES", permissions=[])

        run_purchase_request_permission_seeding()

        role.refresh_from_db()
        assert (
            role.permissions == PURCHASE_REQUEST_ROLE_PERMISSIONS["HUMAN_RESOURCES"]
        )
        for approval_permission in (
            P.DEPARTMENT_HEAD_APPROVE,
            P.ACCOUNTS_VERIFY,
            P.GM_RECOMMEND,
            P.DIRECTOR_APPROVE,
            P.PROCESS,
        ):
            assert approval_permission not in role.permissions

    def test_reverse_removes_only_the_granted_strings(self):
        role = Role.objects.create(
            name="DEPARTMENT_MANAGER", permissions=["hr.view_employee"]
        )
        run_purchase_request_permission_seeding()

        _seed_migration.revoke_purchase_request_permissions(_HistoricalApps(), None)

        role.refresh_from_db()
        assert role.permissions == ["hr.view_employee"]


class TestMigratedPermissionsReachTheLiveApi:
    """
    Section 7/9: the migration - not a permission list handed to a test
    fixture - is what lets a real employee reach the Purchase Request API.
    Every role below is created with no permissions (Case A: exactly what a
    deployment's roles look like before this migration runs).
    """

    def _seeded_client(self, email, role_name, department, employee_code):
        client, employee = employee_client(
            email, role_name, [], department, employee_code
        )
        run_purchase_request_permission_seeding()
        return client, employee

    def test_regular_staff_can_create_list_and_submit_via_migrated_permissions(self):
        it = Department.objects.create(name="IT Department")
        budget_code = AccountChart.objects.create(
            code="4001", name="Hardware", account_type="regular"
        )
        category = PurchaseRequestCategory.objects.create(
            name="Hardware", account_chart=budget_code
        )
        client, requester = self._seeded_client(
            "staff2@zchpc.test", "REGULAR_STAFF", it, "EMP8001"
        )
        # requester_identity() snapshots designation from the employee's
        # position, and the aggregate requires it non-empty - employee_client()
        # does not set one, since none of this file's pre-existing tests hit
        # the create endpoint.
        requester.position = Position.objects.create(title="Officer")
        requester.save(update_fields=["position"])

        create_response = client.post(
            REQUESTS_URL,
            {
                "items": [
                    {
                        "description": "Laptop",
                        "quantity": 1,
                        "expected_delivery_period": "2 weeks",
                        "estimated_cost": "500.00",
                        "category_id": category.id,
                    }
                ]
            },
            format="json",
        )
        assert (
            create_response.status_code == status.HTTP_201_CREATED
        ), create_response.data
        request_id = create_response.data["id"]

        list_response = client.get(REQUESTS_URL)
        assert list_response.status_code == status.HTTP_200_OK

        submit_response = client.post(f"{REQUESTS_URL}{request_id}/submit/")
        assert submit_response.status_code == status.HTTP_200_OK, submit_response.data
        assert submit_response.data["status"] == "PENDING_DEPARTMENT_HEAD"

    def test_procurement_officer_reaches_its_queue_via_migrated_permissions(self):
        it = Department.objects.create(name="IT Department")
        client, _ = self._seeded_client(
            "procurement2@zchpc.test", "PROCUREMENT_OFFICER", it, "EMP8002"
        )

        response = client.get(f"{REQUESTS_URL}?scope=pending-procurement")

        assert response.status_code == status.HTTP_200_OK, response.data

    def test_a_role_outside_the_target_list_still_gets_403_after_seeding_runs(self):
        """
        Seeding having run at all must not become a blanket grant: a role
        this slice does not target stays refused.
        """
        it = Department.objects.create(name="IT Department")
        client, _ = self._seeded_client(
            "sales2@zchpc.test", "SALES_REPRESENTATIVE", it, "EMP8003"
        )

        response = client.get(REQUESTS_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEmployeeDepartmentHeadAccountsChainViaMigratedPermissions:
    """
    Walks Employee -> Department Head -> Accounts end to end using nothing
    but the permissions 0018_seed_purchase_request_permissions actually
    grants - the exact chain this slice exists to make operational.

    Stops at Accounts verification: GM and Director approval have no
    corresponding role in DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS (no
    GENERAL_MANAGER/DIRECTOR role exists in the current role vocabulary), so
    Procurement processing is verified separately, by queue reachability
    only, in TestMigratedPermissionsReachTheLiveApi above.
    """

    def test_full_chain_reaches_accounts_verification(self):
        it = Department.objects.create(name="IT Department")
        budget_code = AccountChart.objects.create(
            code="4002", name="Hardware", account_type="regular"
        )
        category = PurchaseRequestCategory.objects.create(
            name="Hardware", account_chart=budget_code
        )

        staff_client, requester = employee_client(
            "staff3@zchpc.test", "REGULAR_STAFF", [], it, "EMP9001"
        )
        # See the identical note in TestMigratedPermissionsReachTheLiveApi:
        # the aggregate requires a non-empty designation, snapshotted from
        # the employee's position.
        requester.position = Position.objects.create(title="Officer")
        requester.save(update_fields=["position"])
        head_client, head = employee_client(
            "manager2@zchpc.test", "DEPARTMENT_MANAGER", [], it, "EMP9002"
        )
        accounts_client, _accountant = employee_client(
            "accountant2@zchpc.test", "ACCOUNTANT", [], it, "EMP9003"
        )
        it.head = head
        it.save(update_fields=["head"])

        run_purchase_request_permission_seeding()

        create_response = staff_client.post(
            REQUESTS_URL,
            {
                "items": [
                    {
                        "description": "Server rack",
                        "quantity": 1,
                        "expected_delivery_period": "3 weeks",
                        "estimated_cost": "2500.00",
                        "category_id": category.id,
                    }
                ]
            },
            format="json",
        )
        assert (
            create_response.status_code == status.HTTP_201_CREATED
        ), create_response.data
        request_id = create_response.data["id"]

        submit_response = staff_client.post(f"{REQUESTS_URL}{request_id}/submit/")
        assert submit_response.status_code == status.HTTP_200_OK, submit_response.data

        approve_response = head_client.post(
            f"{REQUESTS_URL}{request_id}/department-head/approve/"
        )
        assert (
            approve_response.status_code == status.HTTP_200_OK
        ), approve_response.data
        assert approve_response.data["status"] == "PENDING_ACCOUNTS"

        # Stand-in for Accounts assigning the budget code (a later F25 slice).
        PurchaseRequestItem.objects.filter(purchase_request_id=request_id).update(
            budget_code=budget_code
        )

        verify_response = accounts_client.post(
            f"{REQUESTS_URL}{request_id}/accounts/verify/"
        )
        assert verify_response.status_code == status.HTTP_200_OK, verify_response.data
        assert verify_response.data["status"] == "PENDING_GM"

        record = PurchaseRequestModel.objects.get(pk=request_id)
        assert record.status == "PENDING_GM"
        assert list(
            record.decisions.order_by("created_at").values_list("stage", "decision")
        ) == [
            ("DEPARTMENT_HEAD", "APPROVED"),
            ("ACCOUNTS", "VERIFIED"),
        ]

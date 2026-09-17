"""
Security regression tests for RBACMiddleware route access.

The middleware used to authorize routes from a hard-coded role-name map that
knew nothing about hr.Role.permissions, so a role could hold a Purchase
Request capability and still be refused before reaching it. It now derives
coarse route access from hr.Role.permissions - the same authoritative store
every module's authorization layer reads.

These tests pin down both halves of that contract:

- holding a capability in a module grants entry to that module's routes;
- holding nothing in a module still denies entry, and entry is never a
  substitute for the module's own authorization.

Authentication uses real JWTs, because the middleware runs before DRF's
view-level authentication helpers.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)

pytestmark = pytest.mark.django_db

PROCUREMENT_URL = "/api/v2/procurement/requests/"
HR_URL = "/api/v2/hr/employees/"
PAYROLL_URL = "/api/v2/payroll/payslips/"

User = get_user_model()


@pytest.fixture
def make_user():
    """An authenticated client for an employee holding exactly these permissions."""
    counter = {"n": 0}

    def _make(role_name, permissions, department=None):
        counter["n"] += 1
        role = Role.objects.create(
            name=role_name,
            display_name=role_name.replace("_", " ").title(),
            permissions=list(permissions),
        )
        user = User.objects.create_user(
            email=f"user{counter['n']}@zchpc.test",
            password="RoutePass123!",
            first_name="Test",
            last_name=f"User{counter['n']}",
        )
        employee = Employees.objects.create(
            user=user,
            first_name="Test",
            surname=f"User{counter['n']}",
            email=f"emp{counter['n']}@zchpc.test",
            department=department,
            role=role,
            employee_id=f"EMP{counter['n']:04d}",
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
        return client, employee

    return _make


def reached_application(response):
    """
    Whether the request got past the route gate.

    The two layers are distinguishable by their error shape: RBACMiddleware
    answers with {"detail": ...}, while the application answers with
    {"error": ..., "code": ...}. So a 403 carrying a code was an application
    decision, not a route refusal.
    """
    if response.status_code != status.HTTP_403_FORBIDDEN:
        return True
    return "code" in getattr(response, "data", {})


# =============================================================================
# Purchase Request capabilities reach the API
# =============================================================================


class TestPurchaseRequestCapabilitiesReachTheApi:
    """
    Each workflow capability must get past the route gate on its own.

    These are the roles the legacy map rejected outright. Reaching the API is
    all that is asserted here - whether the operation itself is allowed is
    Slice 4's decision, tested separately.
    """

    @pytest.mark.parametrize(
        "role_name,permission",
        [
            ("REGULAR_STAFF", P.CREATE),
            ("REGULAR_STAFF", P.VIEW),
            ("REGULAR_STAFF", P.SUBMIT),
            ("DEPARTMENT_MANAGER", P.DEPARTMENT_HEAD_APPROVE),
            ("ACCOUNTANT", P.ACCOUNTS_VERIFY),
            ("GENERAL_MANAGER", P.GM_RECOMMEND),
            ("DIRECTOR", P.DIRECTOR_APPROVE),
            ("PROCUREMENT_OFFICER", P.PROCESS),
            ("DEPARTMENT_MANAGER", P.REJECT),
            ("REGULAR_STAFF", P.CORRECT),
            ("REGULAR_STAFF", P.RESUBMIT),
        ],
    )
    def test_capability_holder_is_not_blocked_at_the_route(
        self, make_user, role_name, permission
    ):
        client, _ = make_user(role_name, [permission])

        response = client.get(f"{PROCUREMENT_URL}999999/")

        assert reached_application(response), response.data

    def test_narrow_capability_grants_only_its_own_module(self, make_user):
        """Least privilege: a purchase request capability is not HR access."""
        client, _ = make_user("DEPARTMENT_MANAGER", [P.DEPARTMENT_HEAD_APPROVE])

        assert client.get(HR_URL).status_code == status.HTTP_403_FORBIDDEN
        assert client.get(PAYROLL_URL).status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# Denial is preserved
# =============================================================================


class TestUnauthorizedAccessStillDenied:
    def test_unauthenticated_request_is_rejected(self):
        assert (
            APIClient().get(PROCUREMENT_URL).status_code
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_employee_with_no_permissions_is_denied(self, make_user):
        client, _ = make_user("INTERN", [])

        assert client.get(PROCUREMENT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_employee_with_only_other_module_permissions_is_denied(self, make_user):
        client, _ = make_user("ACCOUNTANT", ["payroll.*", "accounts.*"])

        assert client.get(PROCUREMENT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_user_without_an_employee_profile_is_denied(self):
        """Fail-closed: no employee means no role means no access."""
        user = User.objects.create_user(
            email="profileless@zchpc.test", password="RoutePass123!"
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

        assert client.get(PROCUREMENT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_employee_without_a_role_is_denied(self):
        user = User.objects.create_user(
            email="roleless@zchpc.test", password="RoutePass123!"
        )
        Employees.objects.create(
            user=user,
            first_name="No",
            surname="Role",
            email="norole@zchpc.test",
            employee_id="EMP9001",
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

        assert client.get(PROCUREMENT_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_no_route_became_public(self, make_user):
        """A permissionless employee is refused across every protected family."""
        client, _ = make_user("INTERN", [])

        for url in (PROCUREMENT_URL, HR_URL, PAYROLL_URL):
            assert client.get(url).status_code == status.HTTP_403_FORBIDDEN, url


# =============================================================================
# Access follows permissions, not role names
# =============================================================================


class TestAccessFollowsPermissionsNotRoleNames:
    def test_same_role_category_different_capabilities(self, make_user):
        """
        Two managers, differing only in their granted permissions, get
        different access. Nothing keys off the role name.
        """
        procurement_manager, _ = make_user(
            "DEPARTMENT_MANAGER_A", [P.DEPARTMENT_HEAD_APPROVE]
        )
        hr_manager, _ = make_user("DEPARTMENT_MANAGER_B", ["hr.*"])

        assert reached_application(procurement_manager.get(PROCUREMENT_URL))
        assert not reached_application(hr_manager.get(PROCUREMENT_URL))

        assert reached_application(hr_manager.get(HR_URL))
        assert not reached_application(procurement_manager.get(HR_URL))

    def test_an_unknown_role_name_with_permissions_still_works(self, make_user):
        """The legacy map would have denied this role outright."""
        client, _ = make_user("REGIONAL_STORES_SUPERVISOR", [P.VIEW])

        assert reached_application(client.get(PROCUREMENT_URL))

    def test_module_wildcard_semantics_are_preserved(self, make_user):
        """`procurement.*` still grants the whole procurement family."""
        client, _ = make_user("PROCUREMENT", ["procurement.*"])

        assert reached_application(client.get(PROCUREMENT_URL))

    def test_full_wildcard_grants_every_module(self, make_user):
        client, _ = make_user("ADMIN", ["*"])

        for url in (PROCUREMENT_URL, HR_URL):
            assert reached_application(client.get(url)), url


# =============================================================================
# Reaching the API is not the same as being authorized for the operation
# =============================================================================


class TestRouteAccessIsNotOperationAuthorization:
    def test_capability_holder_is_still_judged_by_slice_4(self, make_user):
        """
        A department head with the capability passes the route gate, then is
        refused by Slice 4 for acting outside the department they head.
        """
        from decimal import Decimal

        from modules.accounts.infrastructure.persistence.models import AccountChart
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequest as PurchaseRequestModel,
            PurchaseRequestItem,
        )

        it = Department.objects.create(name="IT Department")
        finance = Department.objects.create(name="Finance Department")
        budget_code = AccountChart.objects.create(
            code="2001", name="Hardware", account_type="regular"
        )

        _, requester = make_user("REGULAR_STAFF", [P.CREATE], department=it)
        _, it_head = make_user(
            "DEPARTMENT_MANAGER_IT", [P.DEPARTMENT_HEAD_APPROVE], department=it
        )
        wrong_head_client, wrong_head = make_user(
            "DEPARTMENT_MANAGER_FIN", [P.DEPARTMENT_HEAD_APPROVE], department=finance
        )
        it.head = it_head
        it.save(update_fields=["head"])
        finance.head = wrong_head
        finance.save(update_fields=["head"])

        record = PurchaseRequestModel.objects.create(
            requester=requester,
            department=it,
            designation="Developer",
            contact="ext 1",
            status="PENDING_DEPARTMENT_HEAD",
            total_estimated_cost=Decimal("100.00"),
        )
        PurchaseRequestItem.objects.create(
            purchase_request=record,
            description="Item",
            quantity=1,
            expected_delivery_period="1 week",
            estimated_cost=Decimal("100.00"),
            budget_code=budget_code,
        )

        response = wrong_head_client.post(
            f"{PROCUREMENT_URL}{record.id}/department-head/approve/"
        )

        # Refused by Slice 4, not by the route gate - the application error
        # code proves the request got past the middleware.
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "DEPARTMENT_CONTEXT_DENIED"
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT_HEAD"

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

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.procurement.application.authorization import (
    PurchaseRequestPermissions as P,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
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

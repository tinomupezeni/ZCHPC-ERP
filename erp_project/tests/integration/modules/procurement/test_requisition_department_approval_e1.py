"""
E1 (INT-01): fuel and stores department approval by permission and Department.head.

Before E1 the department stage of a fuel or stores requisition was open to
any role whose *name* was or merely contained MANAGER, DEPARTMENT_MANAGER or
HR_MANAGER - so a GENERAL_MANAGER passed on its name alone, and a fuel
requisition could be approved by a manager of any department.

Now the approver must hold the department-head approval capability and be the
recorded head (Department.head) of the requisition's own department. Admins
keep their override; the later stages are unchanged.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from modules.procurement.infrastructure.persistence.models import FuelRequisition, StoresRequisition

pytestmark = pytest.mark.django_db

User = get_user_model()

_numbers = count(78001)

APPROVE = P.DEPARTMENT_HEAD_APPROVE
# Self-service, as every seeded role has: enough to pass RBACMiddleware's
# procurement route gate, so a refusal below comes from the view itself.
SELF_SERVICE = ["portal.*", P.CREATE, P.VIEW]
NOT_AUTHORIZED = "You are not authorized for this approval stage"
NOT_HEAD = "Only the head of the requisition's department can approve this stage"


def make_role(name, permissions):
    role, _ = Role.objects.update_or_create(name=name, defaults={"permissions": list(permissions)})
    return role


def make_employee(label, role=None, department=None, superuser=False):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    create = User.objects.create_superuser if superuser else User.objects.create_user
    user = create(email=email, password="Str0ng-Initial-Passw0rd")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}",
        role=role, department=department,
    )


def client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


@pytest.fixture
def org():
    it = Department.objects.create(name=f"IT {next(_numbers)}")
    finance = Department.objects.create(name=f"Finance {next(_numbers)}")
    head_role = make_role("DEPARTMENT_MANAGER", [*SELF_SERVICE, APPROVE])
    it_head = make_employee("ItHead", head_role, it)
    finance_head = make_employee("FinHead", head_role, finance)
    it.head = it_head
    it.save(update_fields=["head"])
    finance.head = finance_head
    finance.save(update_fields=["head"])
    requester = make_employee("Requester", make_role("REGULAR_STAFF", SELF_SERVICE), it)
    return {"it": it, "finance": finance, "it_head": it_head, "finance_head": finance_head,
            "head_role": head_role, "requester": requester}


def fuel(org):
    return FuelRequisition.objects.create(
        requester=org["requester"].user, department=org["it"], recipient_driver="Driver One",
        vehicle_registration="ABC 1234", purpose="Site visit", destination="Bulawayo",
    )


def stores(org):
    return StoresRequisition.objects.create(
        requester=org["requester"].user, department=org["it"], items=[{"description": "Toner", "quantity": 2}],
    )


def approve(employee, kind, record):
    return client_for(employee).post(f"/api/v2/procurement/{kind}-requisitions/{record.id}/approve/")


def refused_by_view(response, message):
    """403 from the approval view itself, not from the route gate."""
    return response.status_code == 403 and response.json() == {"error": message}


KINDS = [("fuel", fuel, "PENDING_RECIPIENT"), ("stores", stores, "PENDING_PROCUREMENT")]


@pytest.mark.parametrize("kind,make,next_status", KINDS)
class TestDepartmentStage:
    def test_head_of_the_requisitions_department_approves(self, org, kind, make, next_status):
        record = make(org)
        response = approve(org["it_head"], kind, record)

        assert response.status_code == 200, response.data
        record.refresh_from_db()
        assert record.status == next_status
        assert record.department_approved_by_id == org["it_head"].user_id

    def test_head_of_another_department_is_refused(self, org, kind, make, next_status):
        record = make(org)
        response = approve(org["finance_head"], kind, record)

        assert refused_by_view(response, NOT_HEAD)
        record.refresh_from_db()
        assert record.status == "PENDING_DEPARTMENT"

    def test_a_member_with_the_capability_who_is_not_head_is_refused(self, org, kind, make, next_status):
        deputy = make_employee("Deputy", org["head_role"], org["it"])
        assert refused_by_view(approve(deputy, kind, make(org)), NOT_HEAD)

    def test_a_manager_role_name_alone_no_longer_passes(self, org, kind, make, next_status):
        # Names that passed the old match (exact, or containing MANAGER), without the capability.
        for name in ("GENERAL_MANAGER", "MANAGER", "HR_MANAGER"):
            someone = make_employee(name.title(), make_role(name, SELF_SERVICE), org["it"])
            assert refused_by_view(approve(someone, kind, make(org)), NOT_AUTHORIZED), name

    def test_the_head_without_the_capability_is_refused(self, org, kind, make, next_status):
        org["it_head"].role = make_role("HEAD_NO_GRANT", SELF_SERVICE)
        org["it_head"].save(update_fields=["role"])
        assert refused_by_view(approve(org["it_head"], kind, make(org)), NOT_AUTHORIZED)

    def test_admin_keeps_the_override(self, org, kind, make, next_status):
        admin = make_employee("Admin", make_role("ADMIN", ["*"]), superuser=True)
        assert approve(admin, kind, make(org)).status_code == 200

    def test_the_head_cannot_approve_their_own_requisition(self, org, kind, make, next_status):
        record = make(org)
        record.requester = org["it_head"].user
        record.save(update_fields=["requester"])
        assert approve(org["it_head"], kind, record).status_code == 403


def test_later_stages_are_unchanged(org):
    record = stores(org)
    record.status = "PENDING_PROCUREMENT"
    record.save(update_fields=["status"])
    officer = make_employee("Officer", make_role("PROCUREMENT_OFFICER", [*SELF_SERVICE, P.PROCESS]), org["it"])

    response = approve(officer, "stores", record)

    assert response.status_code == 200, response.data
    record.refresh_from_db()
    assert record.status == "PENDING_ACCOUNTS"

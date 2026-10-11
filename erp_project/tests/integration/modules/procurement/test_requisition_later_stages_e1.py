"""
E1 follow-up (INT-01): the later fuel and stores stages match the role name exactly.

E1 fixed the department stage. The later stages (fuel: finance, director,
admin; stores: procurement, accounts, general manager, director, admin) still
passed any role whose name merely *contained* an allowed one - so a
DEPARTMENT_MANAGER passed the stores General Manager stage, whose list holds
MANAGER.

Now each stage takes exactly the roles it listed before, by exact name. Admins
keep their override and the requester still cannot approve their own
requisition.
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

_numbers = count(79001)

# Self-service, as every seeded role has: enough to pass RBACMiddleware's
# procurement route gate, so a refusal below comes from the view itself.
SELF_SERVICE = ["portal.*", P.CREATE, P.VIEW]
NOT_AUTHORIZED = "You are not authorized for this approval stage"
OWN_REQUISITION = "The requester cannot approve their own requisition"

# (kind, status, roles that approve it today, next status)
STAGES = [
    ("fuel", "PENDING_FINANCE", ["FINANCE", "ACCOUNTANT", "GENERAL_MANAGER"], "PENDING_DIRECTOR"),
    ("fuel", "PENDING_DIRECTOR", ["DIRECTOR", "ZCHPC_DIRECTOR"], "PENDING_ADMIN"),
    ("fuel", "PENDING_ADMIN", ["ADMIN", "SYSTEM_ADMINISTRATOR"], "APPROVED"),
    ("stores", "PENDING_PROCUREMENT", ["PROCUREMENT", "PROCUREMENT_OFFICER", "STORES", "STORES_OFFICER"],
     "PENDING_ACCOUNTS"),
    ("stores", "PENDING_ACCOUNTS", ["ACCOUNTS", "ACCOUNTANT", "FINANCE"], "PENDING_GENERAL_MANAGER"),
    ("stores", "PENDING_GENERAL_MANAGER", ["GENERAL_MANAGER", "MANAGER"], "PENDING_DIRECTOR"),
    ("stores", "PENDING_DIRECTOR", ["DIRECTOR", "ZCHPC_DIRECTOR"], "PENDING_ADMIN"),
    ("stores", "PENDING_ADMIN", ["ADMIN", "SYSTEM_ADMINISTRATOR"], "APPROVED"),
]
STAGE_IDS = [f"{kind}-{status}" for kind, status, _, _ in STAGES]
ALLOWED = [(kind, status, role, nxt) for kind, status, roles, nxt in STAGES for role in roles]


def make_role(name, permissions=SELF_SERVICE):
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


@pytest.fixture
def department():
    return Department.objects.create(name=f"IT {next(_numbers)}")


@pytest.fixture
def requester(department):
    return make_employee("Requester", make_role("REGULAR_STAFF"), department)


def requisition(kind, status, requester):
    if kind == "fuel":
        return FuelRequisition.objects.create(
            requester=requester.user, department=requester.department, recipient_driver="Driver One",
            vehicle_registration="ABC 1234", purpose="Site visit", destination="Bulawayo", status=status,
        )
    return StoresRequisition.objects.create(
        requester=requester.user, department=requester.department,
        items=[{"description": "Toner", "quantity": 2}], status=status,
    )


def approve(employee, kind, record):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client.post(f"/api/v2/procurement/{kind}-requisitions/{record.id}/approve/")


def refused_by_view(response, message=NOT_AUTHORIZED):
    """403 from the approval view itself, not from the route gate."""
    return response.status_code == 403 and response.json() == {"error": message}


@pytest.mark.parametrize("kind,status,role,next_status", ALLOWED)
def test_each_stage_keeps_the_roles_it_had(requester, kind, status, role, next_status):
    record = requisition(kind, status, requester)
    approver = make_employee(role.title(), make_role(role), requester.department)

    response = approve(approver, kind, record)

    assert response.status_code == 200, response.data
    record.refresh_from_db()
    assert record.status == next_status


@pytest.mark.parametrize("kind,status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_a_name_that_only_contains_an_allowed_role_is_refused(requester, kind, status, roles, next_status):
    for allowed in roles:
        name = f"ACTING_{allowed}"
        someone = make_employee(name.title(), make_role(name), requester.department)
        record = requisition(kind, status, requester)

        assert refused_by_view(approve(someone, kind, record)), name
        record.refresh_from_db()
        assert record.status == status


def test_a_department_manager_cannot_act_at_the_general_manager_stage(requester):
    # DEPARTMENT_MANAGER contains MANAGER, which is on the stores GM stage's list;
    # it passed that stage before. The head holds the department-stage capability.
    hod = make_employee("Hod", make_role("DEPARTMENT_MANAGER", [*SELF_SERVICE, P.DEPARTMENT_HEAD_APPROVE]),
                        requester.department)
    record = requisition("stores", "PENDING_GENERAL_MANAGER", requester)

    assert refused_by_view(approve(hod, "stores", record))
    record.refresh_from_db()
    assert record.status == "PENDING_GENERAL_MANAGER"
    assert record.general_manager_approved_by_id is None


@pytest.mark.parametrize("kind,status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_admin_keeps_the_override(requester, kind, status, roles, next_status):
    admin = make_employee("Admin", make_role("ADMIN", ["*"]), superuser=True)
    record = requisition(kind, status, requester)

    assert approve(admin, kind, record).status_code == 200
    record.refresh_from_db()
    assert record.status == next_status


@pytest.mark.parametrize("kind,status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_the_requester_cannot_approve_their_own_requisition(department, kind, status, roles, next_status):
    # The requester holds the stage's own role, so only the self-approval rule refuses.
    holder = make_employee("Holder", make_role(roles[0]), department)
    record = requisition(kind, status, holder)

    assert refused_by_view(approve(holder, kind, record), OWN_REQUISITION)
    record.refresh_from_db()
    assert record.status == status

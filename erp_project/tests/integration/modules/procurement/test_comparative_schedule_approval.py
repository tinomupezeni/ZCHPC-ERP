"""
Comparative schedule approval: exact role names and no self-approval.

Each stage (director, procurement, accounts) passed any role whose name merely
*contained* an allowed one, and the requester could approve their own
schedule. Now each stage takes exactly the roles it listed before, by exact
name (as the fuel/stores stages do), and the requester is refused at every
stage, admins included. Admins otherwise keep their override.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from modules.procurement.infrastructure.persistence.models import ComparativeSchedule

pytestmark = pytest.mark.django_db

User = get_user_model()

_numbers = count(83001)

# Self-service, as every seeded role has: enough to pass RBACMiddleware's
# procurement route gate, so a refusal below comes from the view itself.
SELF_SERVICE = ["portal.*", P.CREATE, P.VIEW]
NOT_AUTHORIZED = "You are not authorized for this approval stage"
OWN_SCHEDULE = "The requester cannot approve their own schedule"

# (status, roles that approve it today, next status)
STAGES = [
    ("PENDING_DIRECTOR", ["DIRECTOR", "ZCHPC_DIRECTOR"], "PENDING_PROCUREMENT"),
    ("PENDING_PROCUREMENT", ["PROCUREMENT", "PROCUREMENT_OFFICER"], "PENDING_ACCOUNTS"),
    ("PENDING_ACCOUNTS", ["ACCOUNTS", "ACCOUNTANT", "FINANCE"], "APPROVED"),
]
STAGE_IDS = [status for status, _, _ in STAGES]
ALLOWED = [(status, role, nxt) for status, roles, nxt in STAGES for role in roles]


def make_role(name, permissions=SELF_SERVICE):
    role, _ = Role.objects.update_or_create(name=name, defaults={"permissions": list(permissions)})
    return role


def make_employee(label, role=None, superuser=False):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    create = User.objects.create_superuser if superuser else User.objects.create_user
    user = create(email=email, password="Str0ng-Initial-Passw0rd")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}", role=role,
    )


@pytest.fixture
def requester():
    return make_employee("Requester", make_role("REGULAR_STAFF"))


def schedule(status, requester):
    return ComparativeSchedule.objects.create(requester=requester.user, status=status)


def approve(employee, record):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client.post(f"/api/v2/procurement/comparative-schedules/{record.id}/approve/")


def refused_by_view(response, message=NOT_AUTHORIZED):
    """403 from the approval view itself, not from the route gate."""
    return response.status_code == 403 and response.json() == {"error": message}


@pytest.mark.parametrize("status,role,next_status", ALLOWED)
def test_each_stage_keeps_the_roles_it_had(requester, status, role, next_status):
    record = schedule(status, requester)

    response = approve(make_employee(role.title(), make_role(role)), record)

    assert response.status_code == 200, response.data
    record.refresh_from_db()
    assert record.status == next_status


@pytest.mark.parametrize("status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_a_name_that_only_contains_an_allowed_role_is_refused(requester, status, roles, next_status):
    for allowed in roles:
        name = f"ACTING_{allowed}"
        record = schedule(status, requester)

        assert refused_by_view(approve(make_employee(name.title(), make_role(name)), record)), name
        record.refresh_from_db()
        assert record.status == status


@pytest.mark.parametrize("status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_the_requester_cannot_approve_their_own_schedule(status, roles, next_status):
    # The requester holds the stage's own role, so only the self-approval rule refuses.
    holder = make_employee("Holder", make_role(roles[0]))
    record = schedule(status, holder)

    assert refused_by_view(approve(holder, record), OWN_SCHEDULE)
    record.refresh_from_db()
    assert record.status == status


@pytest.mark.parametrize("status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_an_admin_requester_cannot_approve_their_own_schedule(status, roles, next_status):
    admin = make_employee("Admin", make_role("ADMIN", ["*"]), superuser=True)
    record = schedule(status, admin)

    assert refused_by_view(approve(admin, record), OWN_SCHEDULE)


@pytest.mark.parametrize("status,roles,next_status", STAGES, ids=STAGE_IDS)
def test_admin_keeps_the_override(requester, status, roles, next_status):
    admin = make_employee("Admin", make_role("ADMIN", ["*"]), superuser=True)
    record = schedule(status, requester)

    assert approve(admin, record).status_code == 200
    record.refresh_from_db()
    assert record.status == next_status

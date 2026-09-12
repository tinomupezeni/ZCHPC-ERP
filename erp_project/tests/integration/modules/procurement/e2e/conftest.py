"""
Slice 6 - end-to-end verification of the Purchase Request workflow.

Unlike the Slice 5 API tests, these run against the FULL middleware stack and
obtain credentials from the real login endpoint, so every request traverses:

    HTTP -> JWT auth -> middleware -> API -> Slice 4 authorization
         -> use case -> domain -> repository -> database

Nothing here calls a use case directly, and nothing is force-authenticated.
Assertions check persisted database state, not just status codes.

Role naming
-----------
RBACMiddleware gates /api/v2/procurement/ on the role *name* alone, via the
hard-coded ROLE_PERMISSIONS map, normalising it with
``.upper().replace(" ", "_").replace("-", "_")``. Because hr.Role.name is
unique, several distinct roles can only clear that gate by using different
spellings that normalise onto the same accepted key. That is what these
fixtures do - it lets each actor carry precisely its own Slice 4 capability
while still passing through the real middleware.

That workaround is itself evidence of the production blocker: the middleware
never consults hr.Role.permissions, so genuine roles such as
DEPARTMENT_MANAGER or ACCOUNTANT are still rejected before Slice 4 runs. See
test_purchase_request_rbac_blocker.py.
"""


import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

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

pytestmark = pytest.mark.django_db

REQUESTS_URL = "/api/v2/procurement/requests/"
LOGIN_URL = "/api/v2/auth/token/"
PASSWORD = "IntegrationPass123!"

# Role-name spellings that all normalise to a key RBACMiddleware accepts.
ROLE_SPELLINGS = [
    "PROCUREMENT_OFFICER",
    "Procurement Officer",
    "procurement-officer",
    "Procurement-Officer",
    "procurement officer",
    "PROCUREMENT",
    "Procurement",
]


# =============================================================================
# Test organization
# =============================================================================


@pytest.fixture
def org(db):
    """An isolated organization with realistic employees, roles and budget code."""
    it = Department.objects.create(name="IT Department")
    finance = Department.objects.create(name="Finance Department")
    budget_code = AccountChart.objects.create(
        code="1001", name="Hardware", account_type="regular"
    )

    User = get_user_model()
    spellings = iter(ROLE_SPELLINGS)

    def make(name, title, permissions, department):
        role = Role.objects.create(
            name=next(spellings),
            display_name=title,
            permissions=list(permissions),
        )
        slug = name.lower().replace(" ", ".")
        user = User.objects.create_user(
            email=f"{slug}@zchpc.test",
            password=PASSWORD,
            first_name=name.split()[0],
            last_name=name.split()[-1],
        )
        return Employees.objects.create(
            user=user,
            first_name=name.split()[0],
            surname=name.split()[-1],
            email=f"{slug}.emp@zchpc.test",
            department=department,
            position=Position.objects.create(title=title),
            role=role,
            phone="+263771000111",
        )

    people = {
        "requester": make(
            "Riley Requester",
            "Systems Developer",
            [P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT],
            it,
        ),
        "department_head": make(
            "Hana Head", "IT Manager", [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT], it
        ),
        "accounts": make(
            "Adam Accounts", "Accountant", [P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT], finance
        ),
        "gm": make(
            "Gina Manager", "General Manager", [P.GM_RECOMMEND, P.VIEW, P.REJECT], it
        ),
        "director": make(
            "Dana Director", "Director", [P.DIRECTOR_APPROVE, P.VIEW, P.REJECT], it
        ),
        "procurement": make(
            "Pat Procure", "Procurement Officer", [P.PROCESS, P.VIEW], it
        ),
        "outsider": make("Nora Nobody", "Intern", [], it),
    }

    # The authoritative department-head relationship from Slice 4.
    it.head = people["department_head"]
    it.save(update_fields=["head"])
    finance.head = people["accounts"]
    finance.save(update_fields=["head"])

    return {
        "it": it,
        "finance": finance,
        "budget_code": budget_code,
        **people,
    }


@pytest.fixture
def login():
    """Authenticate through the real login endpoint and return a ready client."""

    def _login(employee):
        client = APIClient()
        response = client.post(
            LOGIN_URL,
            {"email": employee.user.email, "password": PASSWORD},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, (
            f"login failed for {employee.user.email}: "
            f"{response.status_code} {getattr(response, 'data', None)}"
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    return _login


@pytest.fixture
def payload(org):
    """Two line items, so multi-item persistence is actually exercised."""
    return {
        "items": [
            {
                "description": "Dell Latitude 5540 laptop",
                "quantity": 2,
                "expected_delivery_period": "3 weeks",
                "estimated_cost": "3000.00",
                "budget_code_id": org["budget_code"].id,
            },
            {
                "description": "Docking stations",
                "quantity": 2,
                "expected_delivery_period": "3 weeks",
                "estimated_cost": "450.50",
                "budget_code_id": org["budget_code"].id,
            },
        ]
    }


def create_and_submit(login, org, payload):
    """Raise and submit a request as the requester; return its id."""
    client = login(org["requester"])
    created = client.post(REQUESTS_URL, payload, format="json")
    assert created.status_code == status.HTTP_201_CREATED, created.data
    request_id = created.data["id"]

    submitted = client.post(f"{REQUESTS_URL}{request_id}/submit/")
    assert submitted.status_code == status.HTTP_200_OK, submitted.data
    return request_id

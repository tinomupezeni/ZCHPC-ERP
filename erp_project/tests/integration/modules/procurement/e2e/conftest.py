"""
Slice 6 - end-to-end verification of the Purchase Request workflow.

Unlike the Slice 5 API tests, these run against the FULL middleware stack and
obtain credentials from the real login endpoint, so every request traverses:

    HTTP -> JWT auth -> middleware -> API -> Slice 4 authorization
         -> use case -> domain -> repository -> database

Nothing here calls a use case directly, and nothing is force-authenticated.
Assertions check persisted database state, not just status codes.

Roles
-----
Actors use realistic organizational role names (Department Manager, Accountant,
General Manager, Director, Procurement Officer, Regular Staff). Route access is
granted by each role's own hr.Role.permissions, which is what RBACMiddleware
now reads, so no role-name tricks are needed.
"""


import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory,
    PurchaseRequestItem,
)
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

    def make(name, title, role_name, permissions, department):
        role = Role.objects.create(
            name=role_name,
            display_name=role_name.replace("_", " ").title(),
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
            "REGULAR_STAFF",
            [P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT],
            it,
        ),
        "department_head": make(
            "Hana Head",
            "IT Manager",
            "DEPARTMENT_MANAGER",
            [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT],
            it,
        ),
        "accounts": make(
            "Adam Accounts",
            "Accountant",
            "ACCOUNTANT",
            [P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT],
            finance,
        ),
        "gm": make(
            "Gina Manager",
            "General Manager",
            "GENERAL_MANAGER",
            [P.GM_RECOMMEND, P.VIEW, P.REJECT],
            it,
        ),
        "director": make(
            "Dana Director",
            "Director",
            "DIRECTOR",
            [P.DIRECTOR_APPROVE, P.VIEW, P.REJECT],
            it,
        ),
        "procurement": make(
            "Pat Procure",
            "Procurement Officer",
            "PROCUREMENT_OFFICER",
            [P.PROCESS, P.VIEW],
            it,
        ),
        "outsider": make("Nora Nobody", "Intern", "INTERN", [], it),
    }

    # The authoritative department-head relationship from Slice 4.
    it.head = people["department_head"]
    it.save(update_fields=["head"])
    finance.head = people["accounts"]
    finance.save(update_fields=["head"])

    category_account = AccountChart.objects.create(
        code="2001", name="IT Consumables", account_type="regular"
    )
    category = PurchaseRequestCategory.objects.create(
        name="IT Consumables", account_chart=category_account
    )

    return {
        "it": it,
        "finance": finance,
        "budget_code": budget_code,
        "category": category,
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
                "category_id": org["category"].id,
            },
            {
                "description": "Docking stations",
                "quantity": 2,
                "expected_delivery_period": "3 weeks",
                "estimated_cost": "450.50",
                "category_id": org["category"].id,
            },
        ]
    }


def create_and_submit(login, org, payload):
    """Raise and submit a request as the requester; return its id."""
    client = login(org["requester"])
    created = client.post(REQUESTS_URL, payload, format="json")
    assert created.status_code == status.HTTP_201_CREATED, created.data
    request_id = created.data["id"]

    # Stand-in for Accounts assigning the budget code (a later F25 slice):
    # employees never supply one, and Accounts verification requires it.
    PurchaseRequestItem.objects.filter(purchase_request_id=request_id).update(
        budget_code=org["budget_code"]
    )

    submitted = client.post(f"{REQUESTS_URL}{request_id}/submit/")
    assert submitted.status_code == status.HTTP_200_OK, submitted.data
    return request_id

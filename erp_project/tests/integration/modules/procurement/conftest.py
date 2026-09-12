"""
Fixtures for the Purchase Request API tests.

Authentication uses real JWTs rather than force_authenticate, because
middleware runs before DRF's view-level authentication helpers - the same
reason tests/unit/modules/identity/test_security.py does it this way.

Middleware isolation
--------------------
RBACMiddleware gates every /api/v2/procurement/ request against the hard-coded
ROLE_PERMISSIONS map, keyed by role *name*, which grants procurement access to
only four role names. Slice 4's fine-grained capabilities live in a different
store (hr.Role.permissions) and are never consulted there. Since hr.Role.name
is unique, distinct capability sets cannot all share a name the middleware
accepts.

These tests therefore run with that legacy middleware removed, so they exercise
the Slice 5 API boundary and Slice 4 authorization rather than the legacy URL
gate. The gate itself is covered by TestRbacMiddlewareBlocker, which asserts
its current blocking behaviour so the documented blocker stays visible.
"""

from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

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
    PurchaseRequestItem as PurchaseRequestItemModel,
)

User = get_user_model()

LEGACY_URL_GATES = (
    "modules.identity.infrastructure.middleware.RBACMiddleware",
    "modules.identity.infrastructure.middleware.ModuleAccessMiddleware",
)

MIDDLEWARE_WITHOUT_LEGACY_GATES = [
    m for m in settings.MIDDLEWARE if m not in LEGACY_URL_GATES
]


@pytest.fixture
def without_legacy_url_gates():
    """Run the request through everything except the legacy URL-level gates."""
    with override_settings(MIDDLEWARE=MIDDLEWARE_WITHOUT_LEGACY_GATES):
        yield


@pytest.fixture
def anonymous_client():
    """An APIClient carrying no credentials."""
    return APIClient()


@pytest.fixture
def api_url():
    """Base path for the purchase request API."""
    return "/api/v2/procurement/requests/"


@pytest.fixture
def departments(db):
    return {
        "it": Department.objects.create(name="IT Department"),
        "finance": Department.objects.create(name="Finance Department"),
    }


@pytest.fixture
def budget_code(db):
    return AccountChart.objects.create(
        code="1001", name="Hardware", account_type="regular"
    )


@pytest.fixture
def make_employee(db, departments):
    """Create a user + employee + role carrying exactly the given capabilities."""
    counter = {"n": 0}

    def _make(name, permissions, department="it", position="Officer"):
        counter["n"] += 1
        # designation on a purchase request is a snapshot of the employee's
        # position, which the aggregate requires to be non-empty
        position_obj = (
            Position.objects.create(title=f"{position} {counter['n']}")
            if position
            else None
        )
        role = Role.objects.create(
            name=f"TEST_ROLE_{counter['n']}",
            display_name=name,
            permissions=list(permissions),
        )
        slug = name.lower().replace(" ", ".")
        user = User.objects.create_user(
            email=f"{slug}@example.com",
            password="testpass123",
            first_name=name.split()[0],
            last_name=name.split()[-1],
        )
        return Employees.objects.create(
            user=user,
            first_name=name.split()[0],
            surname=name.split()[-1],
            email=f"{slug}.emp@example.com",
            department=departments[department] if department else None,
            position=position_obj,
            role=role,
            phone="+263771000000",
            employee_id=f"EMP{counter['n']:04d}",
        )

    return _make


@pytest.fixture
def client_for():
    """An APIClient authenticated as the given employee's user, via real JWT."""

    def _client(employee):
        client = APIClient()
        token = AccessToken.for_user(employee.user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _client


@pytest.fixture
def requester(make_employee):
    """Ordinary staff member who raises requests."""
    return make_employee(
        "Riley Requester", [P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT]
    )


@pytest.fixture
def department_head(make_employee, departments):
    """The recorded head of the IT department."""
    head = make_employee("Hana Head", [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT])
    departments["it"].head = head
    departments["it"].save(update_fields=["head"])
    return head


@pytest.fixture
def other_department_head(make_employee, departments):
    """Head of Finance - holds the capability, but not for IT's requests."""
    head = make_employee(
        "Owen Other",
        [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT],
        department="finance",
    )
    departments["finance"].head = head
    departments["finance"].save(update_fields=["head"])
    return head


@pytest.fixture
def accountant(make_employee):
    return make_employee("Adam Accounts", [P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT])


@pytest.fixture
def general_manager(make_employee):
    return make_employee("Gina Manager", [P.GM_RECOMMEND, P.VIEW, P.REJECT])


@pytest.fixture
def director(make_employee):
    return make_employee("Dana Director", [P.DIRECTOR_APPROVE, P.VIEW, P.REJECT])


@pytest.fixture
def procurement_officer(make_employee):
    return make_employee("Pat Procure", [P.PROCESS, P.VIEW])


@pytest.fixture
def employee_without_position(make_employee):
    """An employee whose position is unset, so has no designation to snapshot."""
    return make_employee("Polly Positionless", [P.CREATE, P.VIEW], position=None)


@pytest.fixture
def outsider(make_employee):
    """Authenticated employee holding no purchase request capability."""
    return make_employee("Nora Nobody", [])


@pytest.fixture
def make_request_record(db, departments, budget_code):
    """Create a persisted purchase request directly, in a given status."""

    def _make(requester_employee, status="DRAFT", department="it"):
        record = PurchaseRequestModel.objects.create(
            requester=requester_employee,
            department=departments[department],
            designation="Developer",
            contact="ext 123",
            status=status,
            total_estimated_cost=Decimal("1500.00"),
        )
        PurchaseRequestItemModel.objects.create(
            purchase_request=record,
            description="Laptop",
            quantity=1,
            expected_delivery_period="2 weeks",
            estimated_cost=Decimal("1500.00"),
            budget_code=budget_code,
        )
        return record

    return _make


@pytest.fixture
def valid_payload(budget_code):
    """A well-formed create-request body."""
    return {
        "items": [
            {
                "description": "Laptop",
                "quantity": 1,
                "expected_delivery_period": "2 weeks",
                "estimated_cost": "1500.00",
                "budget_code_id": budget_code.id,
            }
        ]
    }

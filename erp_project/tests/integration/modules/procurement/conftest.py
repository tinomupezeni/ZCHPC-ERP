"""
Fixtures for the Purchase Request API tests.

Authentication uses real JWTs rather than force_authenticate, because
middleware runs before DRF's view-level authentication helpers - the same
reason tests/unit/modules/identity/test_security.py does it this way.

Roles
-----
Each actor gets its own role carrying exactly the capability under test.
RBACMiddleware now derives route access from hr.Role.permissions, so holding a
purchase request capability is enough to reach the procurement routes - no
middleware overrides and no role-name tricks are needed.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

import pytest
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
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory as PurchaseRequestCategoryModel,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestItem as PurchaseRequestItemModel,
)

User = get_user_model()

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
def category_url():
    """Base path for the Purchase Request category lookup (Slice F11-A)."""
    return "/api/v2/procurement/purchase-request-categories/"


@pytest.fixture
def category(db):
    """An active Purchase Request category, mapped to its own AccountChart row."""
    account = AccountChart.objects.create(
        code="20000/01/101/021/300", name="IT Consumables", account_type="regular"
    )
    return PurchaseRequestCategoryModel.objects.create(
        name="IT Consumables", account_chart=account, is_active=True
    )


@pytest.fixture
def inactive_category(db):
    """A Purchase Request category that exists but may no longer be selected."""
    account = AccountChart.objects.create(
        code="20000/01/101/022/300", name="Software Subscriptions", account_type="regular"
    )
    return PurchaseRequestCategoryModel.objects.create(
        name="Software Subscriptions", account_chart=account, is_active=False
    )


@pytest.fixture
def make_employee(db, departments):
    """Create a user + employee + role carrying exactly the given capabilities."""
    counter = {"n": 0}

    def _make(
        name, permissions, department="it", position="Officer",
        role_name="STAFF",
    ):
        counter["n"] += 1
        # designation on a purchase request is a snapshot of the employee's
        # position, which the aggregate requires to be non-empty
        position_obj = (
            Position.objects.create(title=f"{position} {counter['n']}")
            if position
            else None
        )
        role = Role.objects.create(
            name=f"{role_name}_{counter['n']}",
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

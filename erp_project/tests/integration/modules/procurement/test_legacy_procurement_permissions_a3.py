"""
A3: the legacy supplier, inventory, budget center and purchase order routes
require the matching permission.

Before A3 any authenticated user who reached the procurement routes - every
staff member does, since raising a purchase request is a procurement
permission - could list, create, edit and delete suppliers, inventory items,
budget centers and purchase orders.

Now reading needs ``procurement.<resource>.view`` and any change needs
``procurement.<resource>.manage``. ``procurement.*`` and ``*`` hold them all.
Calls go through RBACMiddleware with real tokens. Detail routes use an id that
does not exist, so an allowed caller gets 404 and a refused one 403.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.procurement.api.views import LegacyProcurementPermissions as L
from modules.procurement.application.authorization import PurchaseRequestPermissions as P

pytestmark = pytest.mark.django_db

User = get_user_model()

_numbers = count(81001)

BASE = "/api/v2/procurement/"
MISSING = 999999

# Staff self-service, as the evaluation seed grants it (seed_evaluation ROLE_GRANTS).
SELF_SERVICE = ["portal.*", P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT]

# (method, path, body, permission needed, status when allowed)
ROUTES = [
    ("get", "suppliers/", None, L.SUPPLIER_VIEW, 200),
    ("post", "suppliers/", {}, L.SUPPLIER_MANAGE, 400),
    ("get", f"suppliers/{MISSING}/", None, L.SUPPLIER_VIEW, 404),
    ("put", f"suppliers/{MISSING}/", {}, L.SUPPLIER_MANAGE, 404),
    ("delete", f"suppliers/{MISSING}/", None, L.SUPPLIER_MANAGE, 404),
    ("post", f"suppliers/{MISSING}/activate/", None, L.SUPPLIER_MANAGE, 404),
    ("get", "inventory/", None, L.INVENTORY_VIEW, 200),
    ("post", "inventory/", {}, L.INVENTORY_MANAGE, 400),
    ("get", f"inventory/{MISSING}/", None, L.INVENTORY_VIEW, 404),
    ("put", f"inventory/{MISSING}/", {}, L.INVENTORY_MANAGE, 404),
    ("delete", f"inventory/{MISSING}/", None, L.INVENTORY_MANAGE, 404),
    ("get", "budget-centers/", None, L.BUDGET_CENTER_VIEW, 200),
    ("post", "budget-centers/", {}, L.BUDGET_CENTER_MANAGE, 400),
    ("get", f"budget-centers/{MISSING}/", None, L.BUDGET_CENTER_VIEW, 404),
    ("put", f"budget-centers/{MISSING}/", {}, L.BUDGET_CENTER_MANAGE, 404),
    ("delete", f"budget-centers/{MISSING}/", None, L.BUDGET_CENTER_MANAGE, 404),
    ("get", "orders/", None, L.ORDER_VIEW, 200),
    ("get", f"orders/{MISSING}/", None, L.ORDER_VIEW, 404),
    ("post", f"orders/{MISSING}/send/", None, L.ORDER_MANAGE, 404),
    ("post", f"orders/{MISSING}/receive/", {}, L.ORDER_MANAGE, 404),
    ("post", f"orders/{MISSING}/cancel/", {"reason": "x"}, L.ORDER_MANAGE, 404),
]
ROUTE_IDS = [f"{method.upper()} {path}" for method, path, *_ in ROUTES]


def employee_with(permissions, superuser=False):
    n = next(_numbers)
    role = Role.objects.create(name=f"A3_ROLE_{n}", permissions=list(permissions))
    email = f"a3.{n}@zchpc.test"
    create = User.objects.create_superuser if superuser else User.objects.create_user
    user = create(email=email, password="Str0ng-Initial-Passw0rd")
    return Employees.objects.create(
        user=user, first_name="A3", surname=f"Person{n}", email=email, employee_id=f"EMP{n}", role=role,
    )


def call(employee, method, path, body):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return getattr(client, method)(f"{BASE}{path}", body, format="json")


def refused(response, permission):
    return response.status_code == 403 and response.json() == {
        "error": f"Missing required permission '{permission}'"
    }


@pytest.mark.parametrize("method,path,body,permission,allowed_status", ROUTES, ids=ROUTE_IDS)
def test_staff_are_refused(method, path, body, permission, allowed_status):
    assert refused(call(employee_with(SELF_SERVICE), method, path, body), permission)


@pytest.mark.parametrize("method,path,body,permission,allowed_status", ROUTES, ids=ROUTE_IDS)
def test_the_evaluation_procurement_officer_is_refused(method, path, body, permission, allowed_status):
    # The seed's procurement officer only processes purchase requests (A-1).
    officer = employee_with([*SELF_SERVICE, P.PROCESS])
    assert refused(call(officer, method, path, body), permission)


@pytest.mark.parametrize("method,path,body,permission,allowed_status", ROUTES, ids=ROUTE_IDS)
def test_the_matching_permission_is_enough(method, path, body, permission, allowed_status):
    response = call(employee_with([*SELF_SERVICE, permission]), method, path, body)
    assert response.status_code == allowed_status, response.content


@pytest.mark.parametrize("method,path,body,permission,allowed_status", ROUTES, ids=ROUTE_IDS)
def test_legacy_procurement_wildcard_and_admin_keep_access(method, path, body, permission, allowed_status):
    legacy = employee_with(["procurement.*", "identity.*", "portal.*"])  # hr.0017 PROCUREMENT_OFFICER
    admin = employee_with(["*"])
    superuser = employee_with([], superuser=True)
    for who in (legacy, admin, superuser):
        assert call(who, method, path, body).status_code == allowed_status


@pytest.mark.parametrize(
    "view_permission,manage_permission,method,path,body",
    [
        (L.SUPPLIER_VIEW, L.SUPPLIER_MANAGE, "post", "suppliers/", {}),
        (L.INVENTORY_VIEW, L.INVENTORY_MANAGE, "post", "inventory/", {}),
        (L.BUDGET_CENTER_VIEW, L.BUDGET_CENTER_MANAGE, "post", "budget-centers/", {}),
        (L.ORDER_VIEW, L.ORDER_MANAGE, "post", f"orders/{MISSING}/send/", None),
    ],
)
def test_view_does_not_grant_changes(view_permission, manage_permission, method, path, body):
    viewer = employee_with([*SELF_SERVICE, view_permission])
    assert refused(call(viewer, method, path, body), manage_permission)

"""
F25 Slice 1 - migrations 0011-0013: the category backfill.

Historical items only stored the budget code their category resolved to. The
backfill must map budget_code -> category deterministically, keep every
existing budget code, and refuse (rather than guess) if any item cannot be
mapped.
"""

from decimal import Decimal

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("procurement", "0010_purchaserequest_purchase_order_number_and_more")]
AFTER = [("procurement", "0013_purchaserequestitem_category_required")]

pytestmark = pytest.mark.django_db(transaction=True)


def _migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return MigrationExecutor(connection).loader.project_state(targets).apps


@pytest.fixture
def at_0010():
    apps = _migrate(BEFORE)
    yield apps
    # Always leave the test database fully migrated for whatever runs next.
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def _seed_request(apps):
    Department = apps.get_model("hr", "Department")
    Employees = apps.get_model("hr", "Employees")
    PurchaseRequest = apps.get_model("procurement", "PurchaseRequest")
    department = Department.objects.create(name="IT Department")
    employee = Employees.objects.create(
        employee_id="EMPMIG1", email="mig@example.com", department=department
    )
    return PurchaseRequest.objects.create(
        requester=employee,
        department=department,
        designation="Developer",
        contact="ext 1",
        requisition_number="PR-MIG01",
    )


def _account(apps, code):
    return apps.get_model("accounts", "AccountChart").objects.create(
        code=code, name=f"Account {code}", account_type="regular"
    )


def _item(apps, request, budget_code, description="Laptop"):
    return apps.get_model("procurement", "PurchaseRequestItem").objects.create(
        purchase_request=request,
        description=description,
        quantity=1,
        expected_delivery_period="1 week",
        estimated_cost=Decimal("10.00"),
        budget_code=budget_code,
    )


def test_backfill_assigns_the_matching_category_and_keeps_budget_codes(at_0010):
    apps = at_0010
    Category = apps.get_model("procurement", "PurchaseRequestCategory")
    request = _seed_request(apps)
    hardware, travel = _account(apps, "H-1"), _account(apps, "T-1")
    cat_hw = Category.objects.create(name="Hardware", account_chart=hardware)
    cat_tr = Category.objects.create(
        name="Travel", account_chart=travel, is_active=False
    )
    a = _item(apps, request, hardware, "Laptop")
    b = _item(apps, request, hardware, "Mouse")
    c = _item(apps, request, travel, "Flight")

    new_apps = _migrate(AFTER)

    Item = new_apps.get_model("procurement", "PurchaseRequestItem")
    rows = {i.id: i for i in Item.objects.all()}
    assert rows[a.id].category_id == cat_hw.id
    assert rows[b.id].category_id == cat_hw.id
    assert rows[c.id].category_id == cat_tr.id  # inactive categories map too
    assert rows[a.id].budget_code_id == hardware.id
    assert rows[c.id].budget_code_id == travel.id


def test_backfill_aborts_instead_of_guessing_when_an_item_is_unmapped(at_0010):
    apps = at_0010
    request = _seed_request(apps)
    orphan_account = _account(apps, "X-1")  # no category maps to it
    orphan = _item(apps, request, orphan_account)

    with pytest.raises(RuntimeError, match="Cannot backfill"):
        _migrate(AFTER)

    # Remove the unmappable row so the fixture can finish migrating forward.
    apps.get_model("procurement", "PurchaseRequestItem").objects.filter(
        pk=orphan.pk
    ).delete()


def test_budget_code_is_nullable_and_category_required_after_migration(at_0010):
    apps = at_0010
    Category = apps.get_model("procurement", "PurchaseRequestCategory")
    request = _seed_request(apps)
    account = _account(apps, "H-2")
    Category.objects.create(name="Hardware", account_chart=account)
    _item(apps, request, account)

    new_apps = _migrate(AFTER)
    Item = new_apps.get_model("procurement", "PurchaseRequestItem")
    category = new_apps.get_model(
        "procurement", "PurchaseRequestCategory"
    ).objects.get()
    PurchaseRequest = new_apps.get_model("procurement", "PurchaseRequest")

    unassigned = Item.objects.create(
        purchase_request=PurchaseRequest.objects.get(),
        description="Unclassified",
        quantity=1,
        expected_delivery_period="1 week",
        estimated_cost=Decimal("1.00"),
        category=category,
        budget_code=None,
    )
    assert unassigned.budget_code_id is None

    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        Item.objects.create(
            purchase_request=PurchaseRequest.objects.get(),
            description="No category",
            quantity=1,
            expected_delivery_period="1 week",
            estimated_cost=Decimal("1.00"),
            category=None,
        )

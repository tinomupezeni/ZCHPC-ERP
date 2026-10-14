import pytest

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.procurement.infrastructure.persistence.models import FuelRequisition


FUEL_PAYLOAD = {
    "programme": "Workflow test",
    "recipient_driver": "Test Driver",
    "requester_signature": "Test Requester",
    "vehicle_registration": "TEST-001",
    "request_date": "2026-10-08",
    "diesel_quantity": 10,
    "diesel_quantity_words": "Ten litres",
    "petrol_quantity": 0,
    "petrol_quantity_words": "",
    "purpose": "Automated workflow test",
    "destination": "Test destination",
    "destination_dates": "2026-10-09",
}

STORES_PAYLOAD = {
    "items": [
        {
            "description": "Workflow test item",
            "quantity_required": "2",
            "budget_code": "TEST-001",
            "required_by": "2026-10-09",
        }
    ]
}


@pytest.fixture
def create_user(db):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()

    def _create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        is_staff=False,
        is_superuser=False,
        **kwargs,
    ):
        return user_model.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs,
        )

    return _create_user


@pytest.fixture
def requester(create_user, db):
    department = Department.objects.create(name="Workflow Test Department")
    user = create_user(
        email="requester@workflow.test",
        first_name="Test",
        last_name="Requester",
    )
    Employees.objects.create(
        user=user,
        employee_id="EMP9001",
        first_name="Test",
        surname="Requester",
        email=user.email,
        department=department,
    )
    return user


@pytest.fixture
def requester_client(requester):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=requester)
    return client


@pytest.fixture
def create_approver(create_user):
    def _create_approver(role_name, department, employee_id, first_name="Stage", surname="Approver"):
        user = create_user(
            email=f"{employee_id.lower()}@workflow.test",
            first_name=first_name,
            last_name=surname,
        )
        role, _ = Role.objects.get_or_create(name=role_name)
        Employees.objects.create(
            user=user,
            employee_id=employee_id,
            first_name=first_name,
            surname=surname,
            email=user.email,
            department=department,
            role=role,
        )
        return user

    return _create_approver


@pytest.mark.django_db
def test_fuel_requisition_submission_and_approval_flow(requester_client, admin_client):
    response = requester_client.post(
        "/api/v2/portal/fuel-requisitions/", FUEL_PAYLOAD, format="json"
    )

    assert response.status_code == 201, response.data
    assert response.data["status"] == "PENDING_DEPARTMENT"
    assert response.data["requester_name"] == "Test Requester"
    assert response.data["requester_email"] == "requester@workflow.test"
    assert response.data["requester_employee_id"] == "EMP9001"
    requisition_id = response.data["id"]
    approval_url = f"/api/v2/procurement/fuel-requisitions/{requisition_id}/approve/"

    expected_statuses = [
        "PENDING_RECIPIENT",
        "PENDING_FINANCE",
        "PENDING_DIRECTOR",
        "PENDING_ADMIN",
        "APPROVED",
    ]
    for expected_status in expected_statuses:
        approval = admin_client.post(approval_url, {}, format="json")
        assert approval.status_code == 200
        assert approval.data["status"] == expected_status

    history = requester_client.get("/api/v2/portal/fuel-requisitions/")
    assert history.status_code == 200
    completed = history.data[0]
    assert completed["status"] == "APPROVED"
    for stage in ("department", "recipient", "finance", "director", "admin"):
        assert completed[f"{stage}_approved_by"] == "Test User"
        assert completed[f"{stage}_approved_at"] is not None

@pytest.mark.django_db
def test_stores_request_history_is_private_to_requester(requester, requester_client, create_approver):
    requester_client.post(
        "/api/v2/portal/stores-requisitions/", STORES_PAYLOAD, format="json"
    )
    other_user = create_approver(
        "REGULAR_STAFF", requester.employee_profile.department, "EMP9002",
        first_name="Other", surname="Requester",
    )
    from rest_framework.test import APIClient

    other_client = APIClient()
    other_client.force_authenticate(user=other_user)

    history = other_client.get("/api/v2/portal/stores-requisitions/")

    assert history.status_code == 200
    assert history.data == []


@pytest.mark.django_db
def test_fuel_request_history_is_private_to_requester(requester, requester_client, create_approver):
    requester_client.post(
        "/api/v2/portal/fuel-requisitions/", FUEL_PAYLOAD, format="json"
    )
    other_user = create_approver(
        "REGULAR_STAFF", requester.employee_profile.department, "EMP9023",
        first_name="Other", surname="FuelRequester",
    )
    from rest_framework.test import APIClient

    other_client = APIClient()
    other_client.force_authenticate(user=other_user)

    history = other_client.get("/api/v2/portal/fuel-requisitions/")

    assert history.status_code == 200
    assert history.data == []


@pytest.mark.django_db
def test_fuel_requisition_rejects_zero_quantities(requester_client):
    payload = {**FUEL_PAYLOAD, "diesel_quantity": 0, "petrol_quantity": 0}

    response = requester_client.post(
        "/api/v2/portal/fuel-requisitions/", payload, format="json"
    )

    assert response.status_code == 400
    assert response.data["error"] == "Enter a diesel or petrol quantity"


@pytest.mark.django_db
def test_stores_requisition_submission_and_approval_flow(requester_client, admin_client):
    response = requester_client.post(
        "/api/v2/portal/stores-requisitions/", STORES_PAYLOAD, format="json"
    )

    assert response.status_code == 201, response.data
    assert response.data["status"] == "PENDING_DEPARTMENT"
    assert response.data["requester_name"] == "Test Requester"
    assert response.data["requester_email"] == "requester@workflow.test"
    assert response.data["requester_employee_id"] == "EMP9001"
    assert response.data["requisition_number"].startswith("SR-")
    approval_url = (
        f"/api/v2/procurement/stores-requisitions/{response.data['id']}/approve/"
    )

    expected_statuses = [
        "PENDING_PROCUREMENT",
        "PENDING_ACCOUNTS",
        "PENDING_GENERAL_MANAGER",
        "PENDING_DIRECTOR",
        "PENDING_ADMIN",
        "APPROVED",
    ]
    for expected_status in expected_statuses:
        approval = admin_client.post(approval_url, {}, format="json")
        assert approval.status_code == 200
        assert approval.data["status"] == expected_status

    history = requester_client.get("/api/v2/portal/stores-requisitions/")
    assert history.status_code == 200
    assert len(history.data) == 1
    completed = history.data[0]
    assert completed["status"] == "APPROVED"
    assert completed["department_approved_by"] == "Test User"
    assert completed["procurement_approved_by"] == "Test User"
    assert completed["accounts_approved_by"] == "Test User"
    assert completed["general_manager_approved_by"] == "Test User"
    assert completed["director_approved_by"] == "Test User"
    assert completed["admin_approved_by"] == "Test User"
    assert all(completed[f"{stage}_approved_at"] for stage in (
        "department", "procurement", "accounts", "general_manager", "director", "admin"
    ))


@pytest.mark.django_db
def test_stores_requisition_requires_complete_item(requester_client):
    response = requester_client.post(
        "/api/v2/portal/stores-requisitions/",
        {"items": [{"description": "Missing required fields"}]},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("submit_path", "approval_path"),
    [
        (
            "/api/v2/portal/fuel-requisitions/",
            "/api/v2/procurement/fuel-requisitions/{id}/approve/",
        ),
        (
            "/api/v2/portal/stores-requisitions/",
            "/api/v2/procurement/stores-requisitions/{id}/approve/",
        ),
    ],
)
def test_requester_cannot_approve_own_requisition(
    requester_client, submit_path, approval_path
):
    payload = FUEL_PAYLOAD if "fuel" in submit_path else STORES_PAYLOAD
    response = requester_client.post(submit_path, payload, format="json")

    assert response.status_code == 201
    approval = requester_client.post(
        approval_path.format(id=response.data["id"]), {}, format="json"
    )

    assert approval.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("target_status", "role_name", "approver_id", "approver_name"),
    [
        ("PENDING_DEPARTMENT", "DEPARTMENT_MANAGER", "EMP9101", "Department Reviewer"),
        ("PENDING_RECIPIENT", "REGULAR_STAFF", "EMP9102", "Stage Approver"),
        ("PENDING_FINANCE", "GENERAL_MANAGER", "EMP9103", "Finance Reviewer"),
        ("PENDING_DIRECTOR", "DIRECTOR", "EMP9104", "Director Reviewer"),
        ("PENDING_ADMIN", "ADMIN", "EMP9105", "Admin Reviewer"),
    ],
)
def test_fuel_request_can_be_rejected_at_every_office(
    requester, requester_client, admin_client, create_approver,
    target_status, role_name, approver_id, approver_name,
):
    payload = {**FUEL_PAYLOAD, "recipient_driver": approver_name}
    submission = requester_client.post(
        "/api/v2/portal/fuel-requisitions/", payload, format="json"
    )
    assert submission.status_code == 201
    requisition_id = submission.data["id"]
    approval_url = f"/api/v2/procurement/fuel-requisitions/{requisition_id}/approve/"
    rejection_url = f"/api/v2/procurement/fuel-requisitions/{requisition_id}/reject/"

    next_status = {
        "PENDING_DEPARTMENT": "PENDING_RECIPIENT",
        "PENDING_RECIPIENT": "PENDING_FINANCE",
        "PENDING_FINANCE": "PENDING_DIRECTOR",
        "PENDING_DIRECTOR": "PENDING_ADMIN",
    }
    status = "PENDING_DEPARTMENT"
    while status != target_status:
        expected_status = next_status[status]
        advance = admin_client.post(approval_url, {}, format="json")
        assert advance.status_code == 200
        status = advance.data["status"]
        assert status == expected_status

    department = requester.employee_profile.department
    approver = create_approver(
        role_name, department, approver_id,
        first_name=approver_name.split()[0],
        surname=" ".join(approver_name.split()[1:]),
    )
    from rest_framework.test import APIClient

    approver_client = APIClient()
    approver_client.force_authenticate(user=approver)
    inbox = approver_client.get("/api/v2/procurement/fuel-requisitions/inbox/")
    assert inbox.status_code == 200
    assert any(item["id"] == requisition_id for item in inbox.data)

    rejection = approver_client.post(
        rejection_url, {"reason": f"Test rejection at {target_status}"}, format="json"
    )
    assert rejection.status_code == 200
    assert rejection.data["status"] == "REJECTED"
    assert rejection.data["rejected_at_stage"] == target_status

    history = requester_client.get("/api/v2/portal/fuel-requisitions/")
    rejected = next(item for item in history.data if item["id"] == requisition_id)
    assert rejected["status"] == "REJECTED"
    assert rejected["rejected_by"] == f"{approver.first_name} {approver.last_name}"
    assert rejected["rejected_at_stage"] == target_status
    assert rejected["rejection_reason"] == f"Test rejection at {target_status}"
    assert rejected["rejected_at"] is not None
    duplicate_rejection = approver_client.post(
        rejection_url, {"reason": "A second reason"}, format="json"
    )
    after_rejection_approval = admin_client.post(approval_url, {}, format="json")
    assert duplicate_rejection.status_code == 400
    assert after_rejection_approval.status_code == 400
    rejected_record = FuelRequisition.objects.get(pk=requisition_id)
    assert rejected_record.status == "REJECTED"
    assert rejected_record.rejection_reason == f"Test rejection at {target_status}"
    assert rejected_record.rejected_at_stage == target_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("target_status", "role_name", "approver_id", "approver_name"),
    [
        ("PENDING_DEPARTMENT", "DEPARTMENT_MANAGER", "EMP9201", "Department Reviewer"),
        ("PENDING_PROCUREMENT", "PROCUREMENT_OFFICER", "EMP9202", "Procurement Reviewer"),
        ("PENDING_ACCOUNTS", "ACCOUNTANT", "EMP9203", "Finance Reviewer"),
        ("PENDING_GENERAL_MANAGER", "GENERAL_MANAGER", "EMP9204", "General Manager"),
        ("PENDING_DIRECTOR", "DIRECTOR", "EMP9205", "Director Reviewer"),
        ("PENDING_ADMIN", "ADMIN", "EMP9206", "Admin Reviewer"),
    ],
)
def test_stores_request_can_be_rejected_at_every_office(
    requester, requester_client, admin_client, create_approver,
    target_status, role_name, approver_id, approver_name,
):
    submission = requester_client.post(
        "/api/v2/portal/stores-requisitions/", STORES_PAYLOAD, format="json"
    )
    assert submission.status_code == 201
    requisition_id = submission.data["id"]
    approval_url = f"/api/v2/procurement/stores-requisitions/{requisition_id}/approve/"
    rejection_url = f"/api/v2/procurement/stores-requisitions/{requisition_id}/reject/"
    next_status = {
        "PENDING_DEPARTMENT": "PENDING_PROCUREMENT",
        "PENDING_PROCUREMENT": "PENDING_ACCOUNTS",
        "PENDING_ACCOUNTS": "PENDING_GENERAL_MANAGER",
        "PENDING_GENERAL_MANAGER": "PENDING_DIRECTOR",
        "PENDING_DIRECTOR": "PENDING_ADMIN",
    }
    status = "PENDING_DEPARTMENT"
    while status != target_status:
        expected_status = next_status[status]
        advance = admin_client.post(approval_url, {}, format="json")
        assert advance.status_code == 200
        status = advance.data["status"]
        assert status == expected_status

    approver = create_approver(
        role_name, requester.employee_profile.department, approver_id,
        first_name=approver_name.split()[0],
        surname=" ".join(approver_name.split()[1:]),
    )
    from rest_framework.test import APIClient

    approver_client = APIClient()
    approver_client.force_authenticate(user=approver)
    rejection = approver_client.post(
        rejection_url, {"reason": f"Test rejection at {target_status}"}, format="json"
    )
    assert rejection.status_code == 200
    assert rejection.data["status"] == "REJECTED"
    assert rejection.data["rejected_at_stage"] == target_status

    history = requester_client.get("/api/v2/portal/stores-requisitions/")
    rejected = next(item for item in history.data if item["id"] == requisition_id)
    assert rejected["status"] == "REJECTED"
    assert rejected["rejected_by"] == f"{approver.first_name} {approver.last_name}"
    assert rejected["rejected_at_stage"] == target_status
    assert rejected["rejection_reason"] == f"Test rejection at {target_status}"
    assert rejected["rejected_at"] is not None


@pytest.mark.django_db
def test_fuel_inbox_is_department_scoped_and_only_shows_current_stage(
    requester, requester_client, create_approver
):
    submission = requester_client.post(
        "/api/v2/portal/fuel-requisitions/", FUEL_PAYLOAD, format="json"
    )
    requester_department = requester.employee_profile.department
    other_department = Department.objects.create(name="Other Workflow Department")
    manager = create_approver("DEPARTMENT_MANAGER", requester_department, "EMP9002")
    other_manager = create_approver("DEPARTMENT_MANAGER", other_department, "EMP9003")

    from rest_framework.test import APIClient

    manager_client = APIClient()
    manager_client.force_authenticate(user=manager)
    other_manager_client = APIClient()
    other_manager_client.force_authenticate(user=other_manager)

    inbox = manager_client.get("/api/v2/procurement/fuel-requisitions/inbox/")
    other_inbox = other_manager_client.get("/api/v2/procurement/fuel-requisitions/inbox/")

    assert [item["id"] for item in inbox.data] == [submission.data["id"]]
    assert other_inbox.data == []


@pytest.mark.django_db
def test_stores_inbox_is_department_scoped(requester, requester_client, create_approver):
    submission = requester_client.post(
        "/api/v2/portal/stores-requisitions/", STORES_PAYLOAD, format="json"
    )
    requester_department = requester.employee_profile.department
    other_department = Department.objects.create(name="Other Stores Department")
    manager = create_approver("DEPARTMENT_MANAGER", requester_department, "EMP9012")
    other_manager = create_approver("DEPARTMENT_MANAGER", other_department, "EMP9013")

    from rest_framework.test import APIClient

    manager_client = APIClient()
    manager_client.force_authenticate(user=manager)
    other_manager_client = APIClient()
    other_manager_client.force_authenticate(user=other_manager)

    inbox = manager_client.get("/api/v2/procurement/stores-requisitions/inbox/")
    other_inbox = other_manager_client.get("/api/v2/procurement/stores-requisitions/inbox/")

    assert [item["id"] for item in inbox.data] == [submission.data["id"]]
    assert other_inbox.data == []


@pytest.mark.django_db
def test_fuel_recipient_inbox_only_matches_named_driver(
    requester_client, requester, create_approver
):
    payload = {**FUEL_PAYLOAD, "recipient_driver": "Driver Person"}
    submission = requester_client.post(
        "/api/v2/portal/fuel-requisitions/", payload, format="json"
    )
    department = requester.employee_profile.department
    manager = create_approver("DEPARTMENT_MANAGER", department, "EMP9020")
    driver = create_approver(
        "REGULAR_STAFF", department, "EMP9021", first_name="Driver", surname="Person"
    )
    unrelated = create_approver(
        "REGULAR_STAFF", department, "EMP9022", first_name="Other", surname="Person"
    )

    from rest_framework.test import APIClient

    manager_client = APIClient()
    manager_client.force_authenticate(user=manager)
    manager_approval = manager_client.post(
        f"/api/v2/procurement/fuel-requisitions/{submission.data['id']}/approve/",
        {},
        format="json",
    )
    driver_client = APIClient()
    driver_client.force_authenticate(user=driver)
    unrelated_client = APIClient()
    unrelated_client.force_authenticate(user=unrelated)

    assert manager_approval.data["status"] == "PENDING_RECIPIENT"
    driver_inbox = driver_client.get("/api/v2/procurement/fuel-requisitions/inbox/")
    unrelated_inbox = unrelated_client.get("/api/v2/procurement/fuel-requisitions/inbox/")

    assert [item["id"] for item in driver_inbox.data] == [submission.data["id"]]
    assert unrelated_inbox.data == []


@pytest.mark.django_db
def test_regular_employee_can_reach_filtered_requisition_inboxes(requester):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    access_token = str(RefreshToken.for_user(requester).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    fuel_inbox = client.get("/api/v2/procurement/fuel-requisitions/inbox/")
    stores_inbox = client.get("/api/v2/procurement/stores-requisitions/inbox/")

    assert fuel_inbox.status_code == 200
    assert fuel_inbox.data == []
    assert stores_inbox.status_code == 200
    assert stores_inbox.data == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("submit_path", "reject_path", "payload"),
    [
        (
            "/api/v2/portal/fuel-requisitions/",
            "/api/v2/procurement/fuel-requisitions/{id}/reject/",
            FUEL_PAYLOAD,
        ),
        (
            "/api/v2/portal/stores-requisitions/",
            "/api/v2/procurement/stores-requisitions/{id}/reject/",
            STORES_PAYLOAD,
        ),
    ],
)
def test_approver_rejection_records_reason_and_actor(
    requester_client, admin_user, api_client, submit_path, reject_path, payload
):
    submission = requester_client.post(submit_path, payload, format="json")
    api_client.force_authenticate(user=admin_user)
    rejection = api_client.post(
        reject_path.format(id=submission.data["id"]),
        {"reason": "Insufficient supporting information"},
        format="json",
    )

    assert rejection.status_code == 200
    assert rejection.data["status"] == "REJECTED"
    assert rejection.data["rejection_reason"] == "Insufficient supporting information"
    owner_history = requester_client.get(submit_path)
    assert owner_history.status_code == 200
    assert owner_history.data[0]["rejection_reason"] == "Insufficient supporting information"
    assert owner_history.data[0]["rejected_by"] == "Test User"
    assert owner_history.data[0]["rejected_at"] is not None
    if "fuel" in submit_path:
        assert owner_history.data[0]["rejected_at_stage"] == "PENDING_DEPARTMENT"
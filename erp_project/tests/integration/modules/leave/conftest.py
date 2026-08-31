"""
Pytest configuration and fixtures for Leave integration tests.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from modules.identity.infrastructure.persistence.models import CustomUser
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.leave.infrastructure.persistence.models import LeaveType


@pytest.fixture
def auth_client():
    """Create a client authenticated with a real JWT bearer token.

    Uses a bearer token (not force_authenticate) so requests actually pass
    through RBACMiddleware, matching how the browser talks to the API.
    """
    def _auth_client(user):
        client = APIClient()
        if user:
            token = str(RefreshToken.for_user(user).access_token)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client
    return _auth_client


@pytest.fixture
def create_user(db):
    def _create_user(email, is_staff=False, is_superuser=False, **kwargs):
        return CustomUser.objects.create_user(
            email=email, password="testpass123",
            is_staff=is_staff, is_superuser=is_superuser, **kwargs
        )
    return _create_user


@pytest.fixture
def admin_client(create_user, auth_client):
    """Admin/superuser client - deliberately NOT linked to an Employees record."""
    admin = create_user("leave_admin@zchpc.ac.zw", is_staff=True, is_superuser=True)
    return auth_client(admin)


@pytest.fixture
def department(db):
    return Department.objects.create(name="Systems Support")


@pytest.fixture
def employee_client(create_user, auth_client, department):
    """
    Client for a normal user linked to an Employees record.

    RBACMiddleware only grants the "leave.*" permission (needed for
    /api/v2/leave/) to MANAGER/DEPARTMENT_MANAGER/HR/ADMIN roles - plain
    STAFF submits leave through the portal module instead. Give this
    fixture a MANAGER role so it can exercise /api/v2/leave/ directly.
    """
    manager_role, _ = Role.objects.get_or_create(name="MANAGER", defaults={"display_name": "Manager"})
    user = create_user("leave_employee@zchpc.ac.zw")
    employee = Employees.objects.create(
        first_name="Test", surname="Employee", department=department, user=user, role=manager_role
    )
    client = auth_client(user)
    client.employee = employee
    return client


@pytest.fixture
def leave_type(db):
    return LeaveType.objects.create(name="Annual Leave", default_days_allowed=21)

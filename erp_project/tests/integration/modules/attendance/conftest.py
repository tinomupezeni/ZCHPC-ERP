"""
Pytest fixtures for attendance integration tests.
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.infrastructure.persistence.models import CustomUser


@pytest.fixture
def auth_client():
    """Create client authenticated with JWT bearer token."""
    def _auth_client(user):
        client = APIClient()
        if user:
            token = str(RefreshToken.for_user(user).access_token)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client
    return _auth_client


@pytest.fixture
def admin_user(db):
    """Create a superuser (grants access regardless of role)."""
    return CustomUser.objects.create_user(
        email="admin@zchpc.ac.zw",
        password="testpass123",
        first_name="Admin",
        last_name="User",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_client(admin_user, auth_client):
    return auth_client(admin_user)


@pytest.fixture
def staff_user(db):
    """A regular, non-admin user with no employee profile."""
    return CustomUser.objects.create_user(
        email="staff@zchpc.ac.zw",
        password="testpass123",
        first_name="Staff",
        last_name="User",
        is_staff=False,
        is_superuser=False,
    )


@pytest.fixture
def staff_client(staff_user, auth_client):
    return auth_client(staff_user)


@pytest.fixture
def departments(db):
    """Two distinct departments to filter across."""
    return {
        "it": Department.objects.create(name="IT", description="IT department"),
        "applications": Department.objects.create(name="Applications", description="Apps department"),
    }


@pytest.fixture
def employees_with_attendance(db, departments):
    """Two employees in different departments, each with attendance records."""
    today = date.today()

    emp_it = Employees.objects.create(
        first_name="Alice", surname="IT", email="alice@zchpc.ac.zw", department=departments["it"]
    )
    emp_apps = Employees.objects.create(
        first_name="Bob", surname="Apps", email="bob@zchpc.ac.zw", department=departments["applications"]
    )

    AttendanceRecord.objects.create(employee=emp_it, date=today, time_in="08:00", time_out="17:00")
    AttendanceRecord.objects.create(
        employee=emp_it, date=today - timedelta(days=10), time_in="08:00", time_out="17:00"
    )
    AttendanceRecord.objects.create(employee=emp_apps, date=today, time_in="09:00", time_out="17:00")

    return {"it": emp_it, "apps": emp_apps}

"""
Pytest fixtures for recruitment integration tests.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

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

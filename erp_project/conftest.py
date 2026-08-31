"""
Pytest configuration and fixtures for the ERP project.

This file is automatically loaded by pytest and provides:
- Path configuration for src imports
- Django setup
- Shared fixtures for all tests
"""

import sys
from pathlib import Path

import pytest

# Ensure src is in path before Django setup
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Django setup
import django
from django.conf import settings

if not settings.configured:
    django.setup()


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """DRF API client for testing endpoints."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, create_user):
    """API client with authenticated user."""
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def create_user(db):
    """Factory fixture to create test users."""
    from authentication.models import CustomUser

    def _create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        is_staff=False,
        is_superuser=False,
        **kwargs
    ):
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs
        )
        return user

    return _create_user


@pytest.fixture
def admin_user(create_user):
    """Create an admin user."""
    return create_user(
        email='admin@example.com',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def enable_all_system_modules(db):
    """
    Activate every SystemModule row so ModuleAccessMiddleware doesn't block
    requests in tests that aren't specifically exercising the App Store
    install/uninstall flow.
    """
    from modules.identity.infrastructure.persistence.models import SystemModule
    SystemModule.objects.update(is_active=True)


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def db_session(db):
    """
    Provide a database session that rolls back after the test.
    Use for integration tests that need database access.
    """
    from django.db import connection
    yield connection
    # Rollback is handled automatically by pytest-django


# =============================================================================
# Unit Test Helpers (no database)
# =============================================================================

@pytest.fixture
def mock_repository():
    """
    Base mock repository for unit tests.
    Override in specific test modules as needed.
    """
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_event_bus():
    """Mock event bus for unit tests."""
    from unittest.mock import MagicMock
    bus = MagicMock()
    bus.published_events = []

    def publish(event):
        bus.published_events.append(event)

    bus.publish = publish
    return bus

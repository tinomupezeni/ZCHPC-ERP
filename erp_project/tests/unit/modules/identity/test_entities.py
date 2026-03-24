"""
Tests for Identity module entities.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import Email

from modules.identity.domain.entities import AuditEventType, AuditLogEntry, Role, User
from modules.identity.domain.value_objects import HashedPassword, PermissionSet


# =============================================================================
# Test User Entity
# =============================================================================


class TestUser:
    """Tests for User aggregate root."""

    def test_create_user(self):
        """Test user creation with factory method."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        assert user.email.value == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_user_full_name(self):
        """Test full name property."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_user_password_verification(self):
        """Test password verification."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        assert user.verify_password("password123")
        assert not user.verify_password("wrongpassword")

    def test_user_lockout_after_failed_attempts(self):
        """Test account lockout after max failed attempts."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        # Register 4 failed attempts (not locked yet)
        for _ in range(4):
            is_locked = user.register_failed_login()
            assert not is_locked

        # 5th attempt should lock
        is_locked = user.register_failed_login()
        assert is_locked
        assert user.is_locked_out
        assert user.lockout_until is not None

    def test_user_can_login_when_active(self):
        """Test can_login returns true for active user."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        can_login, error = user.can_login()
        assert can_login
        assert error is None

    def test_user_cannot_login_when_deactivated(self):
        """Test can_login returns false for deactivated user."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )
        user.deactivate()

        can_login, error = user.can_login()
        assert not can_login
        assert "deactivated" in error.lower()

    def test_user_unlock(self):
        """Test unlocking a locked user."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        # Lock the user
        for _ in range(5):
            user.register_failed_login()

        assert user.is_locked_out

        # Unlock
        user.unlock()
        assert not user.is_locked_out
        assert user.failed_attempts == 0

    def test_user_password_change(self):
        """Test password change."""
        user = User.create(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
        )

        user.change_password("newpassword456")

        assert not user.verify_password("password123")
        assert user.verify_password("newpassword456")


# =============================================================================
# Test Role Entity
# =============================================================================


class TestRole:
    """Tests for Role aggregate root."""

    def test_create_role(self):
        """Test role creation."""
        role = Role.create(
            id=1,
            name="HR",
            display_name="Human Resources",
            description="HR department role",
            permissions=["hr.*", "employees.*"],
        )

        assert role.name == "HR"
        assert role.display_name == "Human Resources"
        assert role.has_permission("hr.view_employee")

    def test_role_admin_has_all_permissions(self):
        """Test admin role has all permissions."""
        role = Role.create(
            id=1,
            name="ADMIN",
            display_name="Administrator",
            permissions=["*"],
        )

        assert role.is_admin
        assert role.has_permission("anything.at.all")
        assert role.has_permission("hr.delete_employee")

    def test_role_permission_wildcard(self):
        """Test app-level wildcard permissions."""
        role = Role.create(
            id=1,
            name="HR",
            display_name="HR",
            permissions=["hr.*"],
        )

        assert role.has_permission("hr.view_employee")
        assert role.has_permission("hr.create_employee")
        assert not role.has_permission("payroll.process")

    def test_role_grant_permission(self):
        """Test granting new permission."""
        role = Role.create(
            id=1,
            name="STAFF",
            display_name="Staff",
            permissions=["self.*"],
        )

        role.grant_permission("reports.view")
        assert role.has_permission("reports.view")

    def test_role_revoke_permission(self):
        """Test revoking permission."""
        role = Role.create(
            id=1,
            name="STAFF",
            display_name="Staff",
            permissions=["self.*", "reports.view"],
        )

        role.revoke_permission("reports.view")
        assert not role.has_permission("reports.view")


# =============================================================================
# Test AuditLogEntry Entity
# =============================================================================


class TestAuditLogEntry:
    """Tests for AuditLogEntry entity."""

    def test_create_login_success(self):
        """Test creating successful login audit entry."""
        user_id = uuid4()
        entry = AuditLogEntry.create_login_success(
            user_id=user_id,
            email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert entry.user_id == user_id
        assert entry.username_attempted == "test@example.com"
        assert entry.event_type == AuditEventType.LOGIN_SUCCESS
        assert entry.is_success

    def test_create_login_failed(self):
        """Test creating failed login audit entry."""
        entry = AuditLogEntry.create_login_failed(
            email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            reason="Invalid password",
        )

        assert entry.user_id is None
        assert entry.event_type == AuditEventType.LOGIN_FAILED
        assert entry.is_failure
        assert entry.details.get("reason") == "Invalid password"

    def test_create_account_locked(self):
        """Test creating account locked audit entry."""
        user_id = uuid4()
        locked_until = datetime.utcnow() + timedelta(minutes=15)

        entry = AuditLogEntry.create_account_locked(
            user_id=user_id,
            email="test@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            locked_until=locked_until,
        )

        assert entry.event_type == AuditEventType.ACCOUNT_LOCKED
        assert "locked_until" in entry.details

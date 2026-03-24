"""
Tests for Identity module value objects.
"""

import pytest

from shared.domain.exceptions import ValidationError

from modules.identity.domain.value_objects import (
    HashedPassword,
    Permission,
    PermissionSet,
    RoleName,
)


# =============================================================================
# Test HashedPassword
# =============================================================================


class TestHashedPassword:
    """Tests for HashedPassword value object."""

    def test_create_from_plain_text(self):
        """Test creating hashed password from plain text."""
        hashed = HashedPassword.from_plain_text("password123")

        assert hashed.value is not None
        assert hashed.value != "password123"  # Should be hashed
        assert hashed.verify("password123")
        assert not hashed.verify("wrongpassword")

    def test_password_too_short_raises_error(self):
        """Test that short passwords are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HashedPassword.from_plain_text("short")

        assert exc_info.value.code == "PASSWORD_TOO_SHORT"

    def test_empty_password_raises_error(self):
        """Test that empty passwords are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HashedPassword.from_plain_text("")

        assert exc_info.value.code == "EMPTY_PASSWORD"

    def test_from_hash(self):
        """Test creating from existing hash."""
        original = HashedPassword.from_plain_text("password123")
        restored = HashedPassword.from_hash(original.value)

        assert restored.verify("password123")

    def test_str_repr_hides_hash(self):
        """Test that string representation hides the hash."""
        hashed = HashedPassword.from_plain_text("password123")

        assert "password123" not in str(hashed)
        assert "password123" not in repr(hashed)
        assert "***" in str(hashed)


# =============================================================================
# Test Permission
# =============================================================================


class TestPermission:
    """Tests for Permission value object."""

    def test_create_permission(self):
        """Test creating a permission."""
        perm = Permission("hr.view_employee")
        assert perm.value == "hr.view_employee"

    def test_permission_normalized_to_lowercase(self):
        """Test permissions are normalized to lowercase."""
        perm = Permission("HR.View_Employee")
        assert perm.value == "hr.view_employee"

    def test_wildcard_permission(self):
        """Test wildcard permission."""
        perm = Permission("*")
        assert perm.is_wildcard
        assert perm.matches("anything")
        assert perm.matches("hr.view_employee")

    def test_app_wildcard_permission(self):
        """Test app-level wildcard."""
        perm = Permission("hr.*")
        assert perm.is_app_wildcard
        assert perm.app_name == "hr"
        assert perm.matches("hr.view_employee")
        assert perm.matches("hr.delete_employee")
        assert not perm.matches("payroll.process")

    def test_exact_match(self):
        """Test exact permission matching."""
        perm = Permission("hr.view_employee")
        assert perm.matches("hr.view_employee")
        assert not perm.matches("hr.delete_employee")


# =============================================================================
# Test PermissionSet
# =============================================================================


class TestPermissionSet:
    """Tests for PermissionSet value object."""

    def test_create_from_list(self):
        """Test creating permission set from list."""
        perm_set = PermissionSet.from_list(["hr.*", "reports.view"])

        assert len(perm_set) == 2
        assert perm_set.has_permission("hr.view_employee")
        assert perm_set.has_permission("reports.view")
        assert not perm_set.has_permission("payroll.process")

    def test_empty_permission_set(self):
        """Test empty permission set."""
        perm_set = PermissionSet.empty()

        assert len(perm_set) == 0
        assert not perm_set.has_permission("anything")

    def test_full_access_permission_set(self):
        """Test full access permission set."""
        perm_set = PermissionSet.full_access()

        assert perm_set.has_permission("anything")
        assert perm_set.has_permission("hr.delete_employee")

    def test_has_any_permission(self):
        """Test checking for any of multiple permissions."""
        perm_set = PermissionSet.from_list(["hr.*"])

        assert perm_set.has_any_permission(["hr.view", "payroll.process"])
        assert not perm_set.has_any_permission(["payroll.process", "accounts.view"])

    def test_has_all_permissions(self):
        """Test checking for all of multiple permissions."""
        perm_set = PermissionSet.from_list(["hr.*", "payroll.*"])

        assert perm_set.has_all_permissions(["hr.view", "payroll.process"])
        assert not perm_set.has_all_permissions(["hr.view", "accounts.view"])

    def test_in_operator(self):
        """Test 'in' operator for permission checking."""
        perm_set = PermissionSet.from_list(["hr.*"])

        assert "hr.view" in perm_set
        assert "payroll.process" not in perm_set

    def test_iteration(self):
        """Test iterating over permissions."""
        perm_set = PermissionSet.from_list(["hr.*", "reports.view"])

        perms = list(perm_set)
        assert len(perms) == 2

"""
Tests for hr.0019_seed_hr_role's forward/reverse RunPython functions
(REM-05, hardened per review to be deterministic regardless of prior
state).

Same convention as tests/integration/modules/identity
/test_role_permission_seeding.py and tests/integration/modules/procurement
/test_purchase_request_rbac_integration.py's migration-seeding tests:
migration module names start with a digit and cannot be imported with
ordinary import syntax, so the forward/reverse functions are imported via
importlib and called directly against the real Role model - the same
"exercise the migration's own logic against a role the test constructs
first" pattern already established in this repository, rather than
running Django's full migration executor.
"""

from importlib import import_module

import pytest

from modules.hr.infrastructure.persistence.models import Role

_migration = import_module("modules.hr.migrations.0019_seed_hr_role")
ROLE_NAME = _migration.ROLE_NAME
MANAGED_PERMISSION = _migration.MANAGED_PERMISSION
seed_hr_role = _migration.seed_hr_role
unseed_hr_role = _migration.unseed_hr_role

pytestmark = pytest.mark.django_db


class _Apps:
    """Minimal stand-in for the migration's historical model registry."""

    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("hr", "Role")
        return Role


def run_forward():
    seed_hr_role(_Apps(), None)


def run_reverse():
    unseed_hr_role(_Apps(), None)


def clear_pre_existing_hr_role():
    """
    This migration is itself part of the migration graph pytest-django
    replays to build the test database, so HUMAN_RESOURCES already exists
    as baseline data (permissions=[MANAGED_PERMISSION]) before any test in
    this file runs. Each test below wants to control the "before" state
    itself, so it must clear that baseline row first - the same fix
    already applied to tests/integration/modules/identity
    /test_role_permission_seeding.py and tests/integration/modules
    /procurement/test_purchase_request_rbac_integration.py for the same
    reason.
    """
    Role.objects.filter(name=ROLE_NAME).delete()


class TestHrRoleCreatedWhenAbsent:
    def test_absent_role_is_created_with_exactly_the_managed_permission(self):
        clear_pre_existing_hr_role()
        assert not Role.objects.filter(name=ROLE_NAME).exists()

        run_forward()

        role = Role.objects.get(name=ROLE_NAME)
        assert role.permissions == [MANAGED_PERMISSION]
        assert role.display_name == "Human Resources"


class TestHrRoleToppedUpWhenAlreadyPresent:
    def test_existing_role_with_unrelated_permissions_keeps_them_and_gains_the_managed_permission(self):
        clear_pre_existing_hr_role()
        role = Role.objects.create(name=ROLE_NAME, permissions=["some.other.permission"])

        run_forward()

        role.refresh_from_db()
        assert role.permissions == ["some.other.permission", MANAGED_PERMISSION]

    def test_existing_role_already_holding_the_managed_permission_is_unchanged(self):
        clear_pre_existing_hr_role()
        role = Role.objects.create(
            name=ROLE_NAME, permissions=["some.other.permission", MANAGED_PERMISSION]
        )

        run_forward()

        role.refresh_from_db()
        assert role.permissions == ["some.other.permission", MANAGED_PERMISSION]

    def test_running_forward_twice_converges_to_the_same_result(self):
        """Idempotency, exercised directly rather than assumed."""
        run_forward()
        first = list(Role.objects.get(name=ROLE_NAME).permissions)

        run_forward()

        assert list(Role.objects.get(name=ROLE_NAME).permissions) == first


class TestLegacyWildcardIsNotStripped:
    """
    The scenario this migration's own docstring names explicitly: a role
    named HUMAN_RESOURCES that already holds hr.* (e.g. via 0017's still-
    live legacy grant, if it ever ran against a role with this name and
    empty permissions before this migration did). This migration must not
    silently remove that wildcard - only ensure its own managed permission
    is present. Stripping a pre-existing hr.* grant is a separate policy
    decision, out of scope for this migration.
    """

    def test_a_role_already_holding_hr_wildcard_keeps_it_and_gains_the_managed_permission(self):
        clear_pre_existing_hr_role()
        role = Role.objects.create(name=ROLE_NAME, permissions=["hr.*"])

        run_forward()

        role.refresh_from_db()
        assert "hr.*" in role.permissions
        assert MANAGED_PERMISSION in role.permissions
        assert role.permissions == ["hr.*", MANAGED_PERMISSION]


class TestReverseRemovesOnlyTheManagedPermission:
    def test_reverse_removes_the_managed_permission_and_leaves_everything_else(self):
        clear_pre_existing_hr_role()
        role = Role.objects.create(
            name=ROLE_NAME, permissions=["some.other.permission", MANAGED_PERMISSION]
        )

        run_reverse()

        role.refresh_from_db()
        assert role.permissions == ["some.other.permission"]
        # The role row itself is never deleted by reverse - only the one
        # string this migration owns.
        assert Role.objects.filter(name=ROLE_NAME).exists()

    def test_reverse_is_a_no_op_if_the_managed_permission_is_already_absent(self):
        clear_pre_existing_hr_role()
        role = Role.objects.create(name=ROLE_NAME, permissions=["some.other.permission"])

        run_reverse()

        role.refresh_from_db()
        assert role.permissions == ["some.other.permission"]

    def test_reverse_is_a_no_op_if_the_role_does_not_exist(self):
        clear_pre_existing_hr_role()
        assert not Role.objects.filter(name=ROLE_NAME).exists()
        run_reverse()  # must not raise
        assert not Role.objects.filter(name=ROLE_NAME).exists()

"""
Backward-compatibility tests for the role permission seeding migration.

RBACMiddleware used to grant route access from a hard-coded role-name map.
Now that it reads hr.Role.permissions, any role with nothing recorded would
lose the access it previously had. Migration hr.0017 copies the legacy grants
onto such roles.

These tests pin the guarantee the migration makes: existing roles keep exactly
the access they had, and nothing already configured is overwritten.
"""

from importlib import import_module

import pytest

from modules.hr.infrastructure.persistence.models import Role

# Migration module names start with a digit, so they cannot be imported with
# ordinary import syntax.
_migration = import_module("modules.hr.migrations.0017_seed_role_permissions")
LEGACY_ROLE_PERMISSIONS = _migration.LEGACY_ROLE_PERMISSIONS
normalise = _migration.normalise
seed_role_permissions = _migration.seed_role_permissions

pytestmark = pytest.mark.django_db


class _Apps:
    """Minimal stand-in for the migration's historical model registry."""

    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("hr", "Role")
        return Role


def run_seeding():
    seed_role_permissions(_Apps(), None)


class TestLegacyGrantsArePreserved:
    @pytest.mark.parametrize(
        "role_name",
        ["ADMIN", "HUMAN_RESOURCES", "ACCOUNTANT", "DEPARTMENT_MANAGER", "INTERN"],
    )
    def test_empty_role_receives_its_legacy_grants(self, role_name):
        role = Role.objects.create(name=role_name, permissions=[])

        run_seeding()

        role.refresh_from_db()
        assert role.permissions == LEGACY_ROLE_PERMISSIONS[role_name]

    def test_role_name_spelling_variants_are_matched(self):
        """The legacy map's own normalisation is reproduced."""
        role = Role.objects.create(name="Department-Manager", permissions=[])

        run_seeding()

        role.refresh_from_db()
        assert role.permissions == LEGACY_ROLE_PERMISSIONS["DEPARTMENT_MANAGER"]

    def test_configured_permissions_are_never_overwritten(self):
        """An administrator's fine-grained grant survives the migration."""
        configured = ["procurement.purchase_request.department_head_approve"]
        role = Role.objects.create(name="DEPARTMENT_MANAGER", permissions=configured)

        run_seeding()

        role.refresh_from_db()
        assert role.permissions == configured

    def test_roles_unknown_to_the_legacy_map_stay_empty(self):
        """They were denied by the old map too, so they stay denied."""
        role = Role.objects.create(name="REGIONAL_STORES_SUPERVISOR", permissions=[])

        run_seeding()

        role.refresh_from_db()
        assert role.permissions == []

    def test_seeding_is_idempotent(self):
        role = Role.objects.create(name="ACCOUNTANT", permissions=[])

        run_seeding()
        first = list(Role.objects.get(pk=role.pk).permissions)
        run_seeding()

        assert Role.objects.get(pk=role.pk).permissions == first


class TestNormalisation:
    @pytest.mark.parametrize(
        "given,expected",
        [
            ("department manager", "DEPARTMENT_MANAGER"),
            ("Department-Manager", "DEPARTMENT_MANAGER"),
            ("DEPARTMENT_MANAGER", "DEPARTMENT_MANAGER"),
            ("", ""),
        ],
    )
    def test_matches_the_legacy_middleware_normalisation(self, given, expected):
        assert normalise(given) == expected

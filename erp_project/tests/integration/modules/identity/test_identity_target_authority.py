"""
AUD-02 Slice 7B (F7): identity-path target authority.

The established rule (EmployeeAuthorizationPolicy): a mutation of another
account needs the operation's capability AND authority over the target -
the actor's PermissionSet must cover the target's (resolve_actor_permissions:
superuser => full access, otherwise the employee role; a deactivated
employee's role still counts), and the actor may not act on themselves where
the operation forbids it.

Two gaps were found and closed in this slice: renaming another login had no
target check, and creating an employee could attach the new record to an
existing privileged login. An archived employee's login can no longer be
renamed either. Tests marked DECISION record behaviour deliberately left as
it is (is_staff is a platform flag, not part of target authority).
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.identity.application.services import UpdateUserCommand, UserService
from modules.identity.domain.value_objects import PermissionSet
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"

_numbers = count(92001)


def user_url(user_id):
    return f"/api/v2/auth/users/{user_id}/"


def make_user(label, *, staff=False, superuser=False):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        return User.objects.create_superuser(email=email, password=PASSWORD)
    return User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)


def make_employee(label, *permissions, staff=False, superuser=False):
    user = make_user(label, staff=staff, superuser=superuser)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=user.email,
        employee_id=f"EMP{next(_numbers)}", role=role,
    )


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def names(user_id):
    return tuple(User.objects.filter(pk=user_id).values_list("first_name", "last_name").get())


RENAMER = ("hr.employee.view", "hr.employee.create")


# =============================================================================
# Renaming another login (PATCH first_name / last_name)
# =============================================================================


class TestRenameTargetAuthority:
    def test_lower_actor_cannot_rename_a_superuser(self):
        actor = make_employee("Renamer", *RENAMER)
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).patch(
            user_url(root.pk), {"first_name": "Hijacked"}, format="json"
        )
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert names(root.pk) == ("", "")

    def test_lower_actor_cannot_rename_a_higher_role(self):
        actor = make_employee("Renamer", *RENAMER)
        admin = make_employee("Admin", "*")
        response = client_for(actor.user).patch(
            user_url(admin.user_id), {"last_name": "Hijacked"}, format="json"
        )
        assert response.status_code == 403
        assert names(admin.user_id) == ("", "")

    def test_a_deactivated_targets_dormant_role_still_counts(self):
        actor = make_employee("Renamer", *RENAMER)
        admin = make_employee("Admin", "*")
        EmployeeLifecycleService(DjangoEmployeeRepository()).deactivate(admin.pk)
        response = client_for(actor.user).patch(
            user_url(admin.user_id), {"first_name": "Hijacked"}, format="json"
        )
        assert response.status_code == 403

    def test_service_layer_enforces_it_without_http(self):
        root = make_user("Root", superuser=True)
        with pytest.raises(AuthorizationError):
            UserService(DjangoUserRepository()).update_user(
                UpdateUserCommand(user_id=root.pk, first_name="Hijacked"),
                actor_permissions=PermissionSet.from_list(list(RENAMER)),
            )
        assert names(root.pk) == ("", "")

    def test_equal_authority_may_rename(self):
        """covers() is inclusive: holding exactly what the target holds is enough."""
        actor = make_employee("Renamer", *RENAMER)
        peer = make_employee("Peer", *RENAMER)
        response = client_for(actor.user).patch(
            user_url(peer.user_id), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200
        assert names(peer.user_id)[0] == "Renamed"

    def test_higher_actor_may_rename_a_lower_target(self):
        actor = make_employee("Renamer", *RENAMER, "hr.employee.manage_assignments")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).patch(
            user_url(target.user_id), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200

    def test_superuser_may_rename_anyone(self):
        root = make_employee("Root", superuser=True)
        admin = make_employee("Admin", "*")
        response = client_for(root.user).patch(
            user_url(admin.user_id), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200

    def test_anyone_may_rename_themselves(self):
        actor = make_employee("Self", "hr.employee.view")
        response = client_for(actor.user).patch(
            user_url(actor.user_id), {"first_name": "Me"}, format="json"
        )
        assert response.status_code == 200

    def test_an_archived_employees_login_cannot_be_renamed(self):
        """The archived identity is closed (Slice 6), even for a superuser."""
        root = make_employee("Root", superuser=True)
        archived = make_employee("Archived", "hr.employee.view")
        EmployeeLifecycleService(DjangoEmployeeRepository()).archive(archived.pk)
        response = client_for(root.user).patch(
            user_url(archived.user_id), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 400
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"
        assert names(archived.user_id) == ("", "")

    def test_a_deactivated_employees_login_can_still_be_renamed(self):
        root = make_employee("Root", superuser=True)
        target = make_employee("Target", "hr.employee.view")
        EmployeeLifecycleService(DjangoEmployeeRepository()).deactivate(target.pk)
        response = client_for(root.user).patch(
            user_url(target.user_id), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200

    def test_capability_is_still_required(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).patch(
            user_url(target.user_id), {"first_name": "X"}, format="json"
        )
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_CREATE_NOT_AUTHORIZED"


# =============================================================================
# Attaching a new employee record to an existing login (hr employee create)
# =============================================================================


class TestEmployeeCreationAttachingAnExistingLogin:
    """
    modules.hr.signals links a newly created employee to any existing login
    with the same email. That changes the login's identity - it gains an
    employee record, a department, the role given in the request, and from
    then on an employment lifecycle that decides whether it may log in.
    """

    CREATOR = ("hr.employee.view", "hr.employee.create")

    def test_cannot_attach_an_employee_record_to_a_superusers_login(self):
        actor = make_employee("Creator", *self.CREATOR)
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Root", "surname": "Taken", "email": root.email},
            format="json",
        )
        assert response.status_code == 403
        assert not Employees.objects.filter(user_id=root.pk).exists()

    def test_a_refused_attachment_creates_nothing(self):
        actor = make_employee("Creator", *self.CREATOR, "hr.employee.manage_assignments")
        root = make_user("Root", superuser=True)
        employees_before, logins_before = Employees.objects.count(), User.objects.count()
        role = Role.objects.create(name=f"R{next(_numbers)}", permissions=["hr.employee.view"])
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Root", "surname": "Taken", "email": root.email.upper(), "role_id": role.pk},
            format="json",
        )
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert (Employees.objects.count(), User.objects.count()) == (employees_before, logins_before)

    def test_a_covering_actor_may_attach_a_privileged_login(self):
        """A superuser covers another superuser (both hold full access)."""
        actor = make_employee("Root", superuser=True)
        other_root = make_user("Other", superuser=True)
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Other", "surname": "Root", "email": other_root.email},
            format="json",
        )
        assert response.status_code == 201
        assert Employees.objects.get(pk=response.data["id"]).user_id == other_root.pk

    def test_a_staff_only_login_may_be_attached(self):
        """is_staff is not part of target authority (DECISION, Slice 7B)."""
        actor = make_employee("Creator", *self.CREATOR)
        staff = make_user("Staff", staff=True)
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Staff", "surname": "Login", "email": staff.email},
            format="json",
        )
        assert response.status_code == 201
        assert Employees.objects.get(pk=response.data["id"]).user_id == staff.pk

    def test_an_email_already_on_an_employee_keeps_its_conflict(self):
        actor = make_employee("Creator", *self.CREATOR)
        existing = make_employee("Existing", "*")
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Dup", "surname": "Email", "email": existing.email},
            format="json",
        )
        assert response.status_code == 400
        assert response.data["code"] == "DUPLICATE_EMAIL"

    def test_an_unclaimed_login_with_no_authority_may_be_attached(self):
        """A bare, non-privileged login: the actor covers it (it holds nothing)."""
        actor = make_employee("Creator", *self.CREATOR)
        bare = make_user("Bare")
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "Bare", "surname": "Login", "email": bare.email},
            format="json",
        )
        assert response.status_code == 201
        assert Employees.objects.get(pk=response.data["id"]).user_id == bare.pk

    def test_a_new_email_gets_a_new_login(self):
        actor = make_employee("Creator", *self.CREATOR)
        response = client_for(actor.user).post(
            EMPLOYEES_URL,
            {"first_name": "New", "surname": "Hire", "email": "fresh.hire@zchpc.test"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["temporary_password"]

    def test_identity_create_never_attaches_to_an_existing_login(self):
        actor = make_employee("Creator", *self.CREATOR)
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).post(
            "/api/v2/auth/users/",
            {"email": root.email, "first_name": "R", "last_name": "T"},
            format="json",
        )
        assert response.status_code == 409


# =============================================================================
# Already-closed paths, re-checked against the same rule
# =============================================================================


class TestAlreadyEnforced:
    @pytest.mark.parametrize("active", [False, True])
    def test_enable_disable_needs_authority_over_the_target(self, active):
        actor = make_employee(
            "Manager", "hr.employee.view", "hr.employee.deactivate", "hr.employee.reactivate"
        )
        admin = make_employee("Admin", "*")
        if active:
            EmployeeLifecycleService(DjangoEmployeeRepository()).deactivate(admin.pk)
        response = client_for(actor.user).patch(
            user_url(admin.user_id), {"is_active": active}, format="json"
        )
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

    def test_unlock_needs_authority_over_the_target(self):
        actor = make_employee("Unlocker", "hr.employee.view", "hr.employee.reactivate")
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).post(f"{user_url(root.pk)}unlock/")
        assert response.status_code == 403
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

    def test_password_change_only_ever_acts_on_the_caller(self):
        actor = make_employee("Actor", "*")
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).post(
            "/api/v2/auth/password/change/",
            {"current_password": PASSWORD, "new_password": "BrandNewPass456!", "user_id": str(root.pk)},
            format="json",
        )
        assert response.status_code == 200
        root.refresh_from_db()
        assert root.check_password(PASSWORD)


# =============================================================================
# DECISION: platform flags the target-authority model does not express
# =============================================================================


class TestStaffFlagIsNotPartOfTargetAuthority:
    """
    DECISION. resolve_actor_permissions models superuser as full access but
    has no representation of is_staff, so a staff-only login holds "nothing"
    and any capability holder covers it. is_staff currently grants: listing
    every login (/auth/users/), reading the login audit log (/auth/logs/,
    IsAdminUser), and Django admin sign-in. This records today's behaviour.
    """

    def test_a_lifecycle_manager_can_disable_a_staff_only_login(self):
        actor = make_employee("Manager", "hr.employee.view", "hr.employee.deactivate")
        staff = make_user("Staff", staff=True)
        response = client_for(actor.user).patch(
            user_url(staff.pk), {"is_active": False}, format="json"
        )
        assert response.status_code == 200
        assert User.objects.get(pk=staff.pk).is_active is False

    def test_a_creator_can_rename_a_staff_only_login(self):
        actor = make_employee("Renamer", *RENAMER)
        staff = make_user("Staff", staff=True)
        response = client_for(actor.user).patch(
            user_url(staff.pk), {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == 200

"""
AUD-02 F6: who can see another user's account.

GET /api/v2/auth/users/ and GET /api/v2/auth/users/<id>/ share one read
policy (EmployeeAuthorizationPolicy, applied by UserService):

- your own login: always;
- anyone else's: hr.employee.view - an independently assignable capability,
  not implied by any mutation capability and implying none;
- is_staff plays no part; superusers pass through full access;
- a read has no target-authority (covers) check, so a viewer sees accounts
  above them too.

Which logins a viewer sees is the lifecycle rule: enabled always, disabled
with ?include_inactive=true, archived employees' with
?include_archived=true AND hr.employee.view_archived. An archived login is
not found on detail without view_archived.

Every request carries a real JWT, so RBACMiddleware (the coarse "hr" gate
on these routes) is on the path.
"""

from itertools import count
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "VisibilityPass123!"
USERS_URL = "/api/v2/auth/users/"
ME_URL = "/api/v2/auth/users/me/"
ROLES_URL = "/api/v2/hr/roles/"

VIEW = "hr.employee.view"
VIEW_ARCHIVED = "hr.employee.view_archived"
# Every mutation capability on /auth/users/, none of which implies VIEW.
ACCOUNT_MUTATIONS = ["hr.employee.create", "hr.employee.deactivate", "hr.employee.reactivate"]

# EmployeeId accepts only EMP + digits.
_numbers = count(96001)


def user_url(user_id):
    return f"{USERS_URL}{user_id}/"


def make_user(label, *, staff=False, superuser=False):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        return User.objects.create_superuser(email=email, password=PASSWORD)
    return User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)


def make_employee(label, *permissions, staff=False, superuser=False):
    """A login plus employee record whose role grants exactly ``permissions``."""
    user = make_user(label, staff=staff, superuser=superuser)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    return Employees.objects.create(
        user=user,
        first_name=label,
        surname="Person",
        email=user.email,
        role=role,
        employee_id=f"EMP{next(_numbers)}",
    )


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


def deactivated(label="Deactivated"):
    employee = make_employee(label, VIEW)
    lifecycle().deactivate(employee.pk)
    return employee


def archived(label="Archived"):
    employee = make_employee(label, VIEW)
    lifecycle().archive(employee.pk)
    return employee


def listed(user, query=""):
    response = client_for(user).get(f"{USERS_URL}{query}")
    assert response.status_code == status.HTTP_200_OK, response.data
    return {row["email"] for row in response.data}


# =============================================================================
# Holders of hr.employee.view
# =============================================================================


class TestViewerSeesOtherAccounts:
    def test_lists_other_users(self):
        viewer = make_employee("Viewer", VIEW)
        other = make_employee("Other", "procurement.purchase_request.view")
        no_profile = make_user("Noprofile")
        assert {viewer.email, other.email, no_profile.email} <= listed(viewer.user)

    def test_reads_another_users_detail(self):
        viewer = make_employee("Viewer", VIEW)
        other = make_employee("Other", "procurement.purchase_request.view")
        response = client_for(viewer.user).get(user_url(other.user_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == other.email

    def test_reads_a_deactivated_users_detail(self):
        viewer = make_employee("Viewer", VIEW)
        target = deactivated()
        response = client_for(viewer.user).get(user_url(target.user_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_unknown_id_is_not_found(self):
        viewer = make_employee("Viewer", VIEW)
        assert client_for(viewer.user).get(user_url(uuid4())).status_code == 404


class TestSuperuser:
    def test_lists_and_reads_through_full_access(self):
        root = make_user("Root", superuser=True)
        other = make_employee("Other", "procurement.purchase_request.view")
        assert other.email in listed(root)
        assert client_for(root).get(user_url(other.user_id)).status_code == 200

    def test_sees_archived_only_when_asked(self):
        root = make_user("Root", superuser=True)
        target = archived()
        assert target.email not in listed(root, "?include_inactive=true")
        assert target.email in listed(root, "?include_archived=true")


class TestReadsHaveNoTargetAuthority:
    """covers() governs mutations (F7); a read sees accounts above the viewer."""

    def test_viewer_sees_a_superuser_and_a_full_access_role(self):
        viewer = make_employee("Viewer", VIEW)
        root = make_user("Root", superuser=True)
        admin = make_employee("Admin", "*")
        assert {root.email, admin.email} <= listed(viewer.user)
        client = client_for(viewer.user)
        assert client.get(user_url(root.pk)).status_code == status.HTTP_200_OK
        assert client.get(user_url(admin.user_id)).status_code == status.HTTP_200_OK

    def test_seeing_a_privileged_account_grants_no_mutation(self):
        viewer = make_employee("Viewer", VIEW)
        other = make_employee("Other", "procurement.purchase_request.view")
        response = client_for(viewer.user).patch(
            user_url(other.user_id), {"is_active": False}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.get(pk=other.user_id).is_active is True


# =============================================================================
# Without hr.employee.view
# =============================================================================


class TestWithoutTheCapability:
    @pytest.mark.parametrize(
        "permissions",
        [
            ["hr.employee.create"],
            ACCOUNT_MUTATIONS,
            [VIEW_ARCHIVED],
            ["hr.role.manage", "hr.department.manage"],
        ],
        ids=["create", "every-account-mutation", "view-archived-alone", "other-hr"],
    )
    def test_lists_only_themselves(self, permissions):
        actor = make_employee("Actor", *permissions)
        make_employee("Other", VIEW)
        response = client_for(actor.user).get(
            f"{USERS_URL}?include_inactive=true&include_archived=true"
        )
        assert response.status_code == status.HTTP_200_OK
        assert [row["email"] for row in response.data] == [actor.email]

    def test_cannot_read_another_users_detail(self):
        actor = make_employee("Actor", *ACCOUNT_MUTATIONS)
        other = make_employee("Other", VIEW)
        response = client_for(actor.user).get(user_url(other.user_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "EMPLOYEE_VIEW_NOT_AUTHORIZED"

    def test_refusal_does_not_reveal_whether_the_id_exists(self):
        actor = make_employee("Actor", "hr.employee.create")
        target = archived()
        client = client_for(actor.user)
        for user_id in (uuid4(), target.user_id):
            response = client.get(user_url(user_id))
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.data["code"] == "EMPLOYEE_VIEW_NOT_AUTHORIZED"

    def test_reads_their_own_detail(self):
        actor = make_employee("Actor", "hr.employee.create")
        response = client_for(actor.user).get(user_url(actor.user_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == actor.email

    def test_ordinary_user_is_stopped_at_the_gate(self):
        ordinary = make_employee("Ordinary", "procurement.purchase_request.view")
        other = make_employee("Other", VIEW)
        client = client_for(ordinary.user)
        assert client.get(USERS_URL).status_code == status.HTTP_403_FORBIDDEN
        assert client.get(user_url(other.user_id)).status_code == status.HTTP_403_FORBIDDEN


class TestStaffFlagIsNotAReadAuthority:
    def test_staff_without_the_capability_lists_only_themselves(self):
        staff = make_employee("Staff", "hr.employee.create", staff=True)
        make_employee("Other", VIEW)
        response = client_for(staff.user).get(USERS_URL)
        assert [row["email"] for row in response.data] == [staff.email]

    def test_staff_without_the_capability_cannot_read_another_user(self):
        staff = make_employee("Staff", "hr.employee.create", staff=True)
        other = make_employee("Other", VIEW)
        response = client_for(staff.user).get(user_url(other.user_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_without_any_role_is_stopped_at_the_gate(self):
        staff = make_user("Norole", staff=True)
        assert client_for(staff).get(USERS_URL).status_code == status.HTTP_403_FORBIDDEN


class TestMeIsUnchanged:
    @pytest.mark.parametrize("permissions", [[], ["procurement.purchase_request.view"], [VIEW]])
    def test_me_returns_the_caller(self, permissions):
        actor = make_employee("Me", *permissions)
        response = client_for(actor.user).get(ME_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == actor.email

    def test_me_for_a_login_without_an_employee(self):
        user = make_user("Noprofile")
        assert client_for(user).get(ME_URL).data["email"] == user.email


# =============================================================================
# Lifecycle visibility
# =============================================================================


class TestInactiveVisibility:
    def test_deactivated_users_are_left_out_by_default(self):
        viewer = make_employee("Viewer", VIEW)
        target = deactivated()
        assert target.email not in listed(viewer.user)

    def test_include_inactive_adds_deactivated_users(self):
        viewer = make_employee("Viewer", VIEW)
        target = deactivated()
        assert target.email in listed(viewer.user, "?include_inactive=true")

    def test_include_archived_does_not_add_deactivated_users(self):
        viewer = make_employee("Viewer", VIEW, VIEW_ARCHIVED)
        target = deactivated()
        assert target.email not in listed(viewer.user, "?include_archived=true")


class TestArchivedVisibility:
    def test_viewer_without_view_archived_never_lists_archived(self):
        viewer = make_employee("Viewer", VIEW)
        target = archived()
        assert target.email not in listed(
            viewer.user, "?include_inactive=true&include_archived=true"
        )

    def test_view_archived_without_the_opt_in_lists_none(self):
        historian = make_employee("Historian", VIEW, VIEW_ARCHIVED)
        target = archived()
        assert target.email not in listed(historian.user)
        assert target.email not in listed(historian.user, "?include_inactive=true")

    def test_view_and_view_archived_and_the_opt_in_list_archived(self):
        historian = make_employee("Historian", VIEW, VIEW_ARCHIVED)
        target = archived()
        active = make_employee("Active", VIEW)
        emails = listed(historian.user, "?include_archived=true")
        assert {target.email, active.email} <= emails

    def test_archived_detail_without_view_archived_is_not_found(self):
        viewer = make_employee("Viewer", VIEW)
        target = archived()
        client = client_for(viewer.user)
        archived_response = client.get(user_url(target.user_id))
        missing_response = client.get(user_url(uuid4()))
        assert archived_response.status_code == missing_response.status_code == 404
        assert archived_response.data.keys() == missing_response.data.keys()

    def test_archived_detail_with_view_archived(self):
        historian = make_employee("Historian", VIEW, VIEW_ARCHIVED)
        target = archived()
        response = client_for(historian.user).get(user_url(target.user_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == target.email


# =============================================================================
# List and detail share one boundary
# =============================================================================


class TestListAndDetailAgree:
    @pytest.mark.parametrize(
        "permissions, sees_others",
        [([VIEW], True), (ACCOUNT_MUTATIONS, False), ([VIEW_ARCHIVED], False)],
        ids=["view", "mutations-only", "view-archived-only"],
    )
    def test_same_answer_for_list_and_detail(self, permissions, sees_others):
        actor = make_employee("Actor", *permissions)
        other = make_employee("Other", "procurement.purchase_request.view")
        client = client_for(actor.user)
        in_list = other.email in listed(actor.user)
        detail_ok = client.get(user_url(other.user_id)).status_code == status.HTTP_200_OK
        assert in_list is detail_ok is sees_others
        assert actor.email in listed(actor.user)
        assert client.get(user_url(actor.user_id)).status_code == status.HTTP_200_OK


# =============================================================================
# The capability is assigned like any other
# =============================================================================


class TestIndependentAssignment:
    def test_a_role_granting_only_view_is_created_and_works(self):
        role_admin = make_employee("Roleadmin", "hr.role.manage", VIEW)
        response = client_for(role_admin.user).post(
            ROLES_URL,
            {"name": f"USER_VIEWER_{next(_numbers)}", "permissions": [VIEW]},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["permissions"] == [VIEW]

        viewer = make_employee("Viewer")
        Employees.objects.filter(pk=viewer.pk).update(role_id=response.data["id"])
        other = make_employee("Other", "procurement.purchase_request.view")
        assert other.email in listed(viewer.user)

        # Viewing implies no account mutation.
        client = client_for(viewer.user)
        assert client.post(
            USERS_URL,
            {"email": f"new{next(_numbers)}@zchpc.test", "first_name": "N", "last_name": "U"},
            format="json",
        ).status_code == status.HTTP_403_FORBIDDEN
        assert client.patch(
            user_url(other.user_id), {"is_active": False}, format="json"
        ).status_code == status.HTTP_403_FORBIDDEN

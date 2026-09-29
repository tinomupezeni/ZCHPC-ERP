"""
REM-03: leave object-level authorization.

Before this remediation any caller who reached the leave routes could read
and cancel any employee's leave request, read any balance, adjust/set/
initialize anyone's balances, change leave types, review any request, and
(for /requests/pending/) see every pending request in the organization.
/requests/all/ was gated on role names.

Confirmed business rule: review authority comes from leave.request.review
alone - no department, department-head or reporting-line relationship. The
domain's self-review prohibition stays.

Every actor here also holds a harmless "leave.access" permission, only so
RBACMiddleware's coarse "anything in leave.*" gate lets them reach the
routes; it matches none of the leave capabilities. Role names are arbitrary
on purpose.
"""

import itertools
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from modules.leave.api.views import (
    get_leave_balance_service,
    get_leave_request_service,
    get_leave_type_service,
)
from modules.leave.application.authorization import LeaveActor, LeavePermissions as L
from modules.leave.application.services.leave_balance_service import AdjustLeaveBalanceCommand
from modules.leave.application.services.leave_request_service import (
    CancelLeaveRequestCommand,
    ReviewLeaveRequestCommand,
)
from modules.leave.application.services.leave_type_service import CreateLeaveTypeCommand
from modules.leave.infrastructure.persistence.models import (
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()
YEAR = 2026
ROUTE = "leave.access"  # reaches /api/v2/leave/, grants no leave capability
_numbers = itertools.count(1)

PRE_EXISTING_EVENT_BUG = (
    "Pre-existing, out of REM-03 scope: the service constructs a domain event "
    "with keyword arguments the event dataclass does not define "
    "(LeaveTypeCreated(default_days_allowed=...), "
    "LeaveBalanceAdjusted(old_entitled_days=...)), so the operation 400s for "
    "every caller after authorization succeeds. Strict xfail flags the fix."
)
PRE_EXISTING_UPDATE_BUG = (
    "Pre-existing, out of REM-03 scope: LeaveTypeService.update_leave_type "
    "calls LeaveType.update_default_days()/rename(), which the entity does not "
    "define, so every PATCH 400s after authorization succeeds."
)


# ---------------------------------------------------------------- helpers


def make_employee(first, role=None, department=None, reports_to=None):
    n = next(_numbers)
    user = User.objects.create_user(email=f"{first.lower()}{n}@zchpc.test", password="Pass12345!")
    return Employees.objects.create(
        user=user, first_name=first, surname="Tester", email=f"{first.lower()}{n}@zchpc.test",
        employee_id=f"EMP{n:04d}", role=role, department=department, reports_to=reports_to,
    )


def jwt(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def employee_with(*permissions, name="ARBITRARY", **kwargs):
    role = Role.objects.create(name=f"{name}_{next(_numbers)}", permissions=[ROUTE, *permissions])
    employee = make_employee("Actor", role=role, **kwargs)
    return jwt(employee.user), employee


def actor_for(employee, *permissions):
    return LeaveActor(employee_id=employee.pk, permissions=PermissionSet.from_list([ROUTE, *permissions]))


@pytest.fixture
def leave_type():
    return LeaveType.objects.create(name="Annual", default_days_allowed=20)


@pytest.fixture
def victim():
    return make_employee("Victim")


def make_request(employee, leave_type, status_="Pending", reason="VICTIM-SECRET-REASON"):
    return LeaveRequest.objects.create(
        employee=employee, leave_type=leave_type, start_date=date(YEAR, 10, 5),
        end_date=date(YEAR, 10, 7), reason=reason, status=status_,
    )


def make_balance(employee, leave_type, days="20"):
    return LeaveBalance.objects.create(
        employee=employee, leave_type=leave_type, year=YEAR, days_remaining=Decimal(days)
    )


def denied(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, getattr(response, "data", response)


def no_disclosure(response, *secrets):
    body = response.content.decode()
    for s in secrets:
        assert s not in body


# ---------------------------------------------------------------- authentication


class TestUnauthenticated:
    @pytest.mark.parametrize("method, url", [
        ("get", "/api/v2/leave/requests/1/"),
        ("post", "/api/v2/leave/requests/1/cancel/"),
        ("get", "/api/v2/leave/requests/all/"),
        ("get", "/api/v2/leave/requests/pending/"),
        ("post", "/api/v2/leave/balances/initialize/1/"),
    ])
    def test_401(self, method, url):
        assert getattr(APIClient(), method)(url).status_code == status.HTTP_401_UNAUTHORIZED

    def test_service_layer_rejects_anonymous(self, victim, leave_type):
        req = make_request(victim, leave_type)
        with pytest.raises(AuthorizationError) as exc:
            get_leave_request_service().get_leave_request(req.id, LeaveActor.anonymous())
        assert exc.value.code == "UNAUTHENTICATED"


# ---------------------------------------------------------------- request detail / cancel


class TestRequestOwnership:
    def test_employee_can_view_own_request(self, leave_type):
        client, me = employee_with()
        req = make_request(me, leave_type)
        response = client.get(f"/api/v2/leave/requests/{req.id}/")
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_employee_cannot_view_another_employees_request(self, victim, leave_type):
        client, _ = employee_with()
        req = make_request(victim, leave_type)
        response = client.get(f"/api/v2/leave/requests/{req.id}/")
        denied(response)
        no_disclosure(response, "VICTIM-SECRET-REASON")

    def test_missing_and_foreign_requests_are_indistinguishable(self, victim, leave_type):
        client, _ = employee_with()
        req = make_request(victim, leave_type)
        assert client.get(f"/api/v2/leave/requests/{req.id}/").status_code == 403
        assert client.get("/api/v2/leave/requests/999999/").status_code == 403
        assert client.post("/api/v2/leave/requests/999999/cancel/").status_code == 403

    def test_view_any_can_view_another_employees_request_and_gets_404_when_missing(self, victim, leave_type):
        client, _ = employee_with(L.REQUEST_VIEW_ANY)
        req = make_request(victim, leave_type)
        assert client.get(f"/api/v2/leave/requests/{req.id}/").status_code == 200
        assert client.get("/api/v2/leave/requests/999999/").status_code == 404

    def test_employee_can_cancel_own_request(self, leave_type):
        client, me = employee_with()
        req = make_request(me, leave_type)
        response = client.post(f"/api/v2/leave/requests/{req.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK, response.data
        req.refresh_from_db()
        assert req.status == "Cancelled"

    def test_employee_cannot_cancel_another_employees_request(self, victim, leave_type):
        client, _ = employee_with(L.REQUEST_VIEW_ANY, L.REQUEST_REVIEW)
        req = make_request(victim, leave_type)
        denied(client.post(f"/api/v2/leave/requests/{req.id}/cancel/"))
        req.refresh_from_db()
        assert req.status == "Pending"

    def test_cancel_any_can_cancel_another_employees_request(self, victim, leave_type):
        client, _ = employee_with(L.REQUEST_CANCEL_ANY)
        req = make_request(victim, leave_type)
        response = client.post(f"/api/v2/leave/requests/{req.id}/cancel/")
        assert response.status_code == status.HTTP_200_OK, response.data
        req.refresh_from_db()
        assert req.status == "Cancelled"

    def test_cancel_any_still_obeys_the_domain_cancellable_rule(self, victim, leave_type):
        client, _ = employee_with(L.REQUEST_CANCEL_ANY)
        req = make_request(victim, leave_type, status_="Rejected")
        assert client.post(f"/api/v2/leave/requests/{req.id}/cancel/").status_code == 400
        req.refresh_from_db()
        assert req.status == "Rejected"

    def test_service_layer_cancel_denied_without_capability(self, victim, leave_type):
        _, me = employee_with()
        req = make_request(victim, leave_type)
        with pytest.raises(AuthorizationError):
            get_leave_request_service().cancel_leave_request(CancelLeaveRequestCommand(req.id), actor_for(me))
        req.refresh_from_db()
        assert req.status == "Pending"


# ---------------------------------------------------------------- review


class TestReview:
    def review(self, client, req, approved=True):
        return client.post(
            f"/api/v2/leave/requests/{req.id}/review/",
            {"approved": approved, "rejection_reason": "" if approved else "no"}, format="json",
        )

    def test_reviewer_can_approve_another_employees_request(self, victim, leave_type):
        make_balance(victim, leave_type)
        client, _ = employee_with(L.REQUEST_REVIEW)
        req = make_request(victim, leave_type)
        response = self.review(client, req)
        assert response.status_code == status.HTTP_200_OK, response.data
        req.refresh_from_db()
        assert req.status == "Approved"

    def test_reviewer_can_reject(self, victim, leave_type):
        client, _ = employee_with(L.REQUEST_REVIEW)
        req = make_request(victim, leave_type)
        assert self.review(client, req, approved=False).status_code == 200
        req.refresh_from_db()
        assert req.status == "Rejected"

    @pytest.mark.parametrize("approved", [True, False])
    def test_actor_without_review_capability_cannot_review(self, victim, leave_type, approved):
        client, _ = employee_with(L.REQUEST_VIEW_ANY, L.REQUEST_CANCEL_ANY, L.BALANCE_MANAGE, L.TYPE_MANAGE)
        req = make_request(victim, leave_type)
        denied(self.review(client, req, approved))
        req.refresh_from_db()
        assert req.status == "Pending"

    @pytest.mark.parametrize("approved", [True, False])
    def test_reviewer_cannot_review_own_request(self, leave_type, approved):
        client, me = employee_with(L.REQUEST_REVIEW)
        make_balance(me, leave_type)
        req = make_request(me, leave_type)
        response = self.review(client, req, approved)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own leave request" in response.data["error"]
        req.refresh_from_db()
        assert req.status == "Pending"

    def test_caller_supplied_reviewer_id_cannot_bypass_self_review(self, leave_type, victim):
        """Claiming to be someone else so the self-review check compares the wrong id."""
        _, me = employee_with(L.REQUEST_REVIEW)
        req = make_request(me, leave_type)
        with pytest.raises(AuthorizationError) as exc:
            get_leave_request_service().approve_leave_request(
                ReviewLeaveRequestCommand(request_id=req.id, reviewer_id=victim.pk, approved=True),
                actor_for(me, L.REQUEST_REVIEW),
            )
        assert exc.value.code == "LEAVE_REVIEWER_MISMATCH"
        req.refresh_from_db()
        assert req.status == "Pending"

    def test_review_does_not_depend_on_department_or_reporting_line(self, leave_type):
        """
        Reviewer is in a different department, heads no department, and is
        not the requester's manager - capability alone authorizes.
        """
        dept_a, dept_b = Department.objects.create(name="Dept A"), Department.objects.create(name="Dept B")
        head = make_employee("Head", department=dept_a)
        dept_a.head = head
        dept_a.save()
        requester = make_employee("Requester", department=dept_a, reports_to=head)
        make_balance(requester, leave_type)
        client, _ = employee_with(L.REQUEST_REVIEW, department=dept_b)
        req = make_request(requester, leave_type)
        assert self.review(client, req).status_code == 200

    def test_department_head_or_manager_without_capability_cannot_review(self, leave_type):
        dept = Department.objects.create(name="Dept C")
        client, head = employee_with(name="DEPARTMENT_MANAGER", department=dept)
        dept.head = head
        dept.save()
        requester = make_employee("Requester", department=dept, reports_to=head)
        req = make_request(requester, leave_type)
        denied(self.review(client, req))

    def test_missing_request_is_403_without_capability_404_with(self):
        without, _ = employee_with()
        with_cap, _ = employee_with(L.REQUEST_REVIEW)
        body = {"approved": True}
        assert without.post("/api/v2/leave/requests/999999/review/", body, format="json").status_code == 403
        assert with_cap.post("/api/v2/leave/requests/999999/review/", body, format="json").status_code == 404


# ---------------------------------------------------------------- lists


class TestLists:
    @pytest.fixture
    def rows(self, victim, leave_type):
        return make_request(victim, leave_type), make_request(victim, leave_type, status_="Approved")

    def test_all_returns_only_own_for_ordinary_employee(self, rows, leave_type):
        client, me = employee_with()
        mine = make_request(me, leave_type, reason="mine")
        response = client.get("/api/v2/leave/requests/all/")
        assert response.status_code == 200
        assert [r["id"] for r in response.data] == [mine.id]
        no_disclosure(response, "VICTIM-SECRET-REASON")

    def test_all_returns_everything_with_view_any(self, rows, leave_type):
        client, me = employee_with(L.REQUEST_VIEW_ANY)
        make_request(me, leave_type)
        assert len(client.get("/api/v2/leave/requests/all/").data) == 3

    def test_review_capability_alone_does_not_widen_all(self, rows):
        client, _ = employee_with(L.REQUEST_REVIEW)
        assert client.get("/api/v2/leave/requests/all/").data == []

    def test_pending_does_not_leak_to_unprivileged_caller(self, rows, leave_type):
        client, me = employee_with(L.REQUEST_VIEW_ANY)
        mine = make_request(me, leave_type, reason="mine")
        response = client.get("/api/v2/leave/requests/pending/")
        assert [r["id"] for r in response.data] == [mine.id]
        no_disclosure(response, "VICTIM-SECRET-REASON")

    def test_pending_is_the_review_queue_for_reviewers_excluding_own(self, rows, leave_type):
        client, me = employee_with(L.REQUEST_REVIEW)
        make_request(me, leave_type)  # own pending: not reviewable by me
        response = client.get("/api/v2/leave/requests/pending/")
        assert [r["id"] for r in response.data] == [rows[0].id]

    def test_own_list_unchanged(self, rows, leave_type):
        client, me = employee_with()
        mine = make_request(me, leave_type)
        assert [r["id"] for r in client.get("/api/v2/leave/requests/").data] == [mine.id]

    def test_service_layer_blocks_listing_another_employees_requests(self, victim):
        _, me = employee_with()
        service = get_leave_request_service()
        with pytest.raises(AuthorizationError):
            service.get_employee_requests(victim.pk, actor_for(me))
        with pytest.raises(AuthorizationError):
            service.get_request_summary(victim.pk, YEAR, actor_for(me))
        service.get_employee_requests(victim.pk, actor_for(me, L.REQUEST_VIEW_ANY))


# ---------------------------------------------------------------- balances


class TestBalances:
    def test_employee_can_access_own_balance(self, leave_type):
        client, me = employee_with()
        bal = make_balance(me, leave_type)
        assert client.get(f"/api/v2/leave/balances/{bal.id}/").status_code == 200
        assert client.get(f"/api/v2/leave/balances/?year={YEAR}").status_code == 200

    def test_employee_cannot_access_another_employees_balance(self, victim, leave_type):
        client, _ = employee_with()
        bal = make_balance(victim, leave_type, days="17.5")
        response = client.get(f"/api/v2/leave/balances/{bal.id}/")
        denied(response)
        no_disclosure(response, "17.5")
        assert client.get("/api/v2/leave/balances/999999/").status_code == 403

    def test_view_any_can_access_another_employees_balance(self, victim, leave_type):
        client, _ = employee_with(L.BALANCE_VIEW_ANY)
        bal = make_balance(victim, leave_type)
        assert client.get(f"/api/v2/leave/balances/{bal.id}/").status_code == 200

    def test_adjust_requires_manage_and_does_not_persist(self, victim, leave_type):
        bal = make_balance(victim, leave_type)
        client, _ = employee_with(L.BALANCE_VIEW_ANY)
        denied(client.post(f"/api/v2/leave/balances/{bal.id}/adjust/",
                           {"adjustment_days": "30", "reason": "x"}, format="json"))
        bal.refresh_from_db()
        assert bal.days_remaining == Decimal("20")

    def test_adjust_own_balance_also_requires_manage(self, leave_type):
        client, me = employee_with()
        bal = make_balance(me, leave_type)
        denied(client.post(f"/api/v2/leave/balances/{bal.id}/adjust/",
                           {"adjustment_days": "30", "reason": "x"}, format="json"))
        bal.refresh_from_db()
        assert bal.days_remaining == Decimal("20")

    def test_manage_passes_adjust_authorization(self, victim, leave_type):
        bal = make_balance(victim, leave_type)
        client, _ = employee_with(L.BALANCE_MANAGE)
        response = client.post(f"/api/v2/leave/balances/{bal.id}/adjust/",
                               {"adjustment_days": "5", "reason": "x"}, format="json")
        assert response.status_code != 403, response.data
        assert "code" not in response.data  # not an authorization failure

    @pytest.mark.xfail(strict=True, reason=PRE_EXISTING_EVENT_BUG)
    def test_manage_can_adjust(self, victim, leave_type):
        bal = make_balance(victim, leave_type)
        client, _ = employee_with(L.BALANCE_MANAGE)
        response = client.post(f"/api/v2/leave/balances/{bal.id}/adjust/",
                               {"adjustment_days": "5", "reason": "x"}, format="json")
        assert response.status_code == 200, response.data

    def test_set_entitlement_requires_manage(self, victim, leave_type):
        body = {"employee_id": victim.pk, "leave_type_id": leave_type.id, "year": YEAR, "entitled_days": "99"}
        client, _ = employee_with(L.BALANCE_VIEW_ANY)
        denied(client.post("/api/v2/leave/balances/admin/", body, format="json"))
        assert not LeaveBalance.objects.filter(employee=victim).exists()
        manager, _ = employee_with(L.BALANCE_MANAGE)
        assert manager.post("/api/v2/leave/balances/admin/", body, format="json").status_code == 201

    def test_initialize_requires_manage_even_for_self(self, victim, leave_type):
        client, me = employee_with()
        denied(client.post(f"/api/v2/leave/balances/initialize/{me.pk}/", {}, format="json"))
        denied(client.post(f"/api/v2/leave/balances/initialize/{victim.pk}/", {}, format="json"))
        assert not LeaveBalance.objects.exists()

    def test_manage_can_initialize(self, victim, leave_type):
        client, _ = employee_with(L.BALANCE_MANAGE)
        response = client.post(f"/api/v2/leave/balances/initialize/{victim.pk}/", {"year": YEAR}, format="json")
        assert response.status_code == 201, response.data
        assert LeaveBalance.objects.filter(employee=victim).count() == 1

    def test_service_layer_adjuster_id_cannot_be_spoofed(self, victim, leave_type):
        bal = make_balance(victim, leave_type)
        _, me = employee_with()
        with pytest.raises(AuthorizationError):
            get_leave_balance_service().adjust_balance(
                AdjustLeaveBalanceCommand(bal.id, Decimal("1"), "x", adjusted_by_id=victim.pk),
                actor_for(me, L.BALANCE_MANAGE),
            )
        with pytest.raises(AuthorizationError):
            get_leave_balance_service().get_all_balances(victim.pk, YEAR, actor_for(me))


# ---------------------------------------------------------------- leave types


class TestLeaveTypes:
    def test_reads_unchanged_for_any_route_holder(self, leave_type):
        client, _ = employee_with()
        assert client.get("/api/v2/leave/types/").status_code == 200
        assert client.get(f"/api/v2/leave/types/{leave_type.id}/").status_code == 200

    def test_unauthorized_actor_cannot_mutate(self, leave_type):
        client, _ = employee_with(L.BALANCE_MANAGE, L.REQUEST_REVIEW)
        denied(client.post("/api/v2/leave/types/", {"name": "Sneaky", "default_days_allowed": 99}, format="json"))
        denied(client.patch(f"/api/v2/leave/types/{leave_type.id}/", {"default_days_allowed": 99}, format="json"))
        denied(client.delete(f"/api/v2/leave/types/{leave_type.id}/"))
        leave_type.refresh_from_db()
        assert leave_type.default_days_allowed == 20
        assert not LeaveType.objects.filter(name="Sneaky").exists()

    def test_authorized_actor_can_mutate(self, leave_type):
        client, _ = employee_with(L.TYPE_MANAGE)
        created = client.post("/api/v2/leave/types/", {"name": "Study", "default_days_allowed": 5}, format="json")
        assert created.status_code != 403 and "code" not in created.data, created.data
        patched = client.patch(f"/api/v2/leave/types/{leave_type.id}/", {"default_days_allowed": 21}, format="json")
        assert patched.status_code != 403 and "code" not in patched.data, patched.data
        disposable = LeaveType.objects.create(name="Disposable", default_days_allowed=1)
        assert client.delete(f"/api/v2/leave/types/{disposable.id}/").status_code == 204
        assert not LeaveType.objects.filter(id=disposable.id).exists()

    @pytest.mark.xfail(strict=True, reason=PRE_EXISTING_UPDATE_BUG)
    def test_authorized_actor_can_update(self, leave_type):
        client, _ = employee_with(L.TYPE_MANAGE)
        assert client.patch(f"/api/v2/leave/types/{leave_type.id}/", {"default_days_allowed": 21},
                            format="json").status_code == 200

    @pytest.mark.xfail(strict=True, reason=PRE_EXISTING_EVENT_BUG)
    def test_authorized_actor_can_create(self):
        client, _ = employee_with(L.TYPE_MANAGE)
        assert client.post("/api/v2/leave/types/", {"name": "Study", "default_days_allowed": 5},
                           format="json").status_code == 201

    def test_service_layer_denies(self):
        _, me = employee_with()
        with pytest.raises(AuthorizationError):
            get_leave_type_service().create_leave_type(CreateLeaveTypeCommand(name="X"), actor_for(me))


# ---------------------------------------------------------------- role names, wildcard, superuser


class TestRoleNamesWildcardsSuperuser:
    @pytest.mark.parametrize("role_name", ["HR", "HUMAN_RESOURCES", "MANAGER", "ADMIN"])
    def test_role_names_grant_nothing(self, role_name, victim, leave_type):
        client, _ = employee_with(name=role_name)
        req = make_request(victim, leave_type)
        denied(client.get(f"/api/v2/leave/requests/{req.id}/"))
        denied(client.post(f"/api/v2/leave/requests/{req.id}/review/", {"approved": True}, format="json"))
        assert client.get("/api/v2/leave/requests/all/").data == []

    def test_is_staff_alone_grants_nothing(self, victim, leave_type):
        client, me = employee_with()
        me.user.is_staff = True
        me.user.save()
        req = make_request(victim, leave_type)
        assert client.get("/api/v2/leave/requests/all/").data == []
        denied(client.post(f"/api/v2/leave/requests/{req.id}/review/", {"approved": True}, format="json"))

    def test_leave_wildcard_grants_everything(self, victim, leave_type):
        make_balance(victim, leave_type)
        role = Role.objects.create(name=f"W_{next(_numbers)}", permissions=["leave.*"])
        client = jwt(make_employee("Wild", role=role).user)
        req = make_request(victim, leave_type)
        assert client.get(f"/api/v2/leave/requests/{req.id}/").status_code == 200
        assert len(client.get("/api/v2/leave/requests/all/").data) == 1
        assert client.post(f"/api/v2/leave/requests/{req.id}/review/", {"approved": True},
                           format="json").status_code == 200

    def test_unlinked_superuser_retains_access(self, victim, leave_type):
        make_balance(victim, leave_type)
        client = jwt(User.objects.create_superuser(email=f"rem03.su{next(_numbers)}@zchpc.test", password="x"))
        req = make_request(victim, leave_type)
        other = make_request(victim, leave_type)
        assert client.get(f"/api/v2/leave/requests/{req.id}/").status_code == 200
        assert len(client.get("/api/v2/leave/requests/all/").data) == 2
        assert len(client.get("/api/v2/leave/requests/pending/").data) == 2
        assert client.post(f"/api/v2/leave/requests/{req.id}/review/", {"approved": True},
                           format="json").status_code == 200
        assert client.post(f"/api/v2/leave/requests/{other.id}/cancel/").status_code == 200
        assert client.post(f"/api/v2/leave/balances/initialize/{victim.pk}/", {"year": YEAR + 1},
                           format="json").status_code == 201
        disposable = LeaveType.objects.create(name="SU-Disposable", default_days_allowed=1)
        assert client.delete(f"/api/v2/leave/types/{disposable.id}/").status_code == 204

    def test_unlinked_non_superuser_gets_nothing(self, victim, leave_type):
        user = User.objects.create_user(email=f"unlinked{next(_numbers)}@zchpc.test", password="x", is_staff=True)
        req = make_request(victim, leave_type)
        # No employee -> no role -> RBACMiddleware refuses the route outright.
        assert jwt(user).get(f"/api/v2/leave/requests/{req.id}/").status_code == 403


# ---------------------------------------------------------------- alternate path: portal stays self-scoped


class TestPortalRemainsSelfScoped:
    def test_portal_cancel_cannot_touch_another_employees_request(self, victim, leave_type):
        role = Role.objects.create(name=f"P_{next(_numbers)}", permissions=["portal.*"])
        client = jwt(make_employee("Portal", role=role).user)
        from django.urls import resolve

        req = make_request(victim, leave_type)
        url = f"/api/v2/portal/leave/requests/{req.id}/"
        assert resolve(url).url_name == "leave-request-cancel"  # the real portal cancel route
        # The portal provider is schema-stale (orders by a non-existent
        # created_at field - pre-existing, tracked separately), so this may be
        # a 500 rather than a clean refusal. Either way nothing is cancelled.
        client.raise_request_exception = False
        response = client.delete(url)
        assert response.status_code != 200
        req.refresh_from_db()
        assert req.status == "Pending"

"""
AUD-02 Slice 7A: durable lifecycle audit.

Every transition that changes an employee's lifecycle state writes exactly
one hr.EmployeeLifecycleEvent, inside the same transaction:

    who (actor login + email), which employee (row + EC number), when,
    from and to which state, why (optional reason), through which API
    (source), and what accompanied it (login effect; for an archive, the
    department headships vacated).

No record is written when nothing changes, when the transition is refused,
or when the transaction rolls back. Records are append-only.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence import lifecycle_events
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import (
    Department,
    EmployeeLifecycleEvent,
    Employees,
    Role,
)
from modules.identity.application import services as identity_services
from modules.procurement.infrastructure.persistence.models import PurchaseRequest

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmployeePass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
ADMIN_CAPABILITIES = [
    "hr.employee.view",
    "hr.employee.deactivate",
    "hr.employee.reactivate",
    "hr.employee.archive",
]

_numbers = count(94001)


# =============================================================================
# Helpers
# =============================================================================


def make_employee(label, *permissions, superuser=False, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
        user = User.objects.create_user(email=email, password=PASSWORD)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    extra.setdefault("employee_id", f"EMP{next(_numbers)}")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role, **extra
    )


def admin():
    return make_employee("Admin", *ADMIN_CAPABILITIES)


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def events(employee):
    return list(EmployeeLifecycleEvent.objects.filter(employee_id=employee.pk))


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


def hr_deactivate(client, employee, **body):
    return client.delete(f"{EMPLOYEES_URL}{employee.pk}/", body, format="json")


def hr_reactivate(client, employee, **body):
    return client.post(f"{EMPLOYEES_URL}{employee.pk}/reactivate/", body, format="json")


def hr_archive(client, employee, **body):
    return client.post(f"{EMPLOYEES_URL}{employee.pk}/archive/", body, format="json")


def identity_set_active(client, employee, active):
    return client.patch(
        f"/api/v2/auth/users/{employee.user_id}/", {"is_active": active}, format="json"
    )


def state(employee):
    row = Employees.objects.get(pk=employee.pk)
    login = User.objects.get(pk=row.user_id).is_active if row.user_id else None
    return (row.lifecycle_status, login)


# =============================================================================
# One record per real transition, through every path
# =============================================================================


class TestEachTransitionIsRecordedOnce:
    def test_hr_deactivation(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        response = hr_deactivate(client_for(actor.user), target, reason="Suspended pending review")
        assert response.status_code == 200

        [event] = events(target)
        assert (event.event_type, event.from_status, event.to_status) == (
            "DEACTIVATE", "ACTIVE", "DEACTIVATED",
        )
        assert (event.actor_id, event.actor_email) == (actor.user_id, actor.email)
        assert event.employee_number == target.employee_id
        assert event.reason == "Suspended pending review"
        assert event.source == "hr.employee.deactivate"
        assert event.details == {"login": "disabled"}
        assert event.occurred_at is not None

    def test_hr_reactivation(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        response = hr_reactivate(client_for(actor.user), target, reason="Returned from leave")
        assert response.status_code == 200

        event = events(target)[-1]
        assert (event.event_type, event.from_status, event.to_status) == (
            "REACTIVATE", "DEACTIVATED", "ACTIVE",
        )
        assert event.actor_id == actor.user_id
        assert event.reason == "Returned from leave"
        assert event.source == "hr.employee.reactivate"
        assert event.details == {"login": "enabled"}

    @pytest.mark.parametrize("start", ["ACTIVE", "DEACTIVATED"])
    def test_archive_from_either_state(self, start):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        if start == "DEACTIVATED":
            lifecycle().deactivate(target.pk)
        response = hr_archive(client_for(actor.user), target, reason="Left the organisation")
        assert response.status_code == 200

        event = events(target)[-1]
        assert (event.event_type, event.from_status, event.to_status) == (
            "ARCHIVE", start, "ARCHIVED",
        )
        assert event.actor_id == actor.user_id
        assert event.reason == "Left the organisation"
        assert event.source == "hr.employee.archive"
        assert event.details == {
            "login": "disabled" if start == "ACTIVE" else "unchanged",
            "vacated_department_headships": [],
        }

    def test_archive_records_the_headships_it_vacated(self):
        actor = make_employee("Admin", *ADMIN_CAPABILITIES)
        head = make_employee("Head", "hr.employee.view")
        first = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        second = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        response = hr_archive(client_for(actor.user), head, vacate_department_headships=True)
        assert response.status_code == 200
        [event] = events(head)
        assert event.details["vacated_department_headships"] == sorted([first.pk, second.pk])

    @pytest.mark.parametrize("active,event_type", [(False, "DEACTIVATE"), (True, "REACTIVATE")])
    def test_identity_path_is_recorded_with_its_actor(self, active, event_type):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        if active:
            lifecycle().deactivate(target.pk)
        response = identity_set_active(client_for(actor.user), target, active)
        assert response.status_code == 200
        event = events(target)[-1]
        assert event.event_type == event_type
        assert (event.actor_id, event.source) == (actor.user_id, "identity.user.update")
        assert event.reason == ""

    def test_actor_without_an_employee_record_is_recorded(self):
        root = User.objects.create_superuser(email="bare.root@zchpc.test", password=PASSWORD)
        target = make_employee("Target", "hr.employee.view")
        hr_deactivate(client_for(root), target)
        [event] = events(target)
        assert (event.actor_id, event.actor_email) == (root.pk, "bare.root@zchpc.test")

    def test_direct_service_use_has_no_actor(self):
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        [event] = events(target)
        assert (event.actor_id, event.actor_email, event.source) == (None, "", "")

    def test_employee_without_a_login(self):
        actor = admin()
        target = make_employee("Nologin", "hr.employee.view")
        Employees.objects.filter(pk=target.pk).update(user=None)
        hr_deactivate(client_for(actor.user), target)
        assert events(target)[0].details == {"login": "no_login"}

    def test_a_full_lifecycle_reads_back_in_order(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        hr_deactivate(client, target)
        hr_reactivate(client, target)
        hr_archive(client, target)
        assert [(e.event_type, e.from_status, e.to_status) for e in events(target)] == [
            ("DEACTIVATE", "ACTIVE", "DEACTIVATED"),
            ("REACTIVATE", "DEACTIVATED", "ACTIVE"),
            ("ARCHIVE", "ACTIVE", "ARCHIVED"),
        ]


class TestReasonInput:
    @pytest.mark.parametrize("path", [hr_deactivate, hr_reactivate, hr_archive])
    def test_a_non_text_reason_is_refused_and_nothing_happens(self, path):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        if path is hr_reactivate:
            lifecycle().deactivate(target.pk)
        before = (state(target), len(events(target)))
        response = path(client_for(actor.user), target, reason=["not", "text"])
        assert response.status_code == 400
        assert response.data["code"] == "INVALID_REQUEST"
        assert (state(target), len(events(target))) == before

    def test_reason_is_optional_and_trimmed(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        hr_deactivate(client, target, reason="  spaced  ")
        hr_reactivate(client, target)
        assert [e.reason for e in events(target)] == ["spaced", ""]


# =============================================================================
# Nothing is recorded unless the state changed
# =============================================================================


class TestNothingRecordedWithoutAStateChange:
    def test_repeated_requests(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        hr_deactivate(client, target)
        hr_deactivate(client, target)
        hr_reactivate(client, target)
        hr_reactivate(client, target)
        hr_archive(client, target)
        hr_archive(client, target)
        assert [e.event_type for e in events(target)] == ["DEACTIVATE", "REACTIVATE", "ARCHIVE"]

    def test_a_login_repair_without_a_state_change_is_not_a_lifecycle_event(self):
        target = make_employee("Target", "hr.employee.view")
        Employees.objects.filter(pk=target.pk).update(lifecycle_status="DEACTIVATED", is_active=False)
        lifecycle().deactivate(target.pk)
        assert state(target) == ("DEACTIVATED", False)
        assert events(target) == []

    @pytest.mark.parametrize("path", ["hr_reactivate", "hr_deactivate", "identity_on", "identity_off"])
    def test_refused_transitions_out_of_archived(self, path):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        lifecycle().archive(target.pk)
        before = len(events(target))
        client = client_for(actor.user)
        response = {
            "hr_reactivate": lambda: hr_reactivate(client, target),
            "hr_deactivate": lambda: hr_deactivate(client, target),
            "identity_on": lambda: identity_set_active(client, target, True),
            "identity_off": lambda: identity_set_active(client, target, False),
        }[path]()
        assert response.status_code == 400
        assert len(events(target)) == before

    @pytest.mark.parametrize("path", [hr_deactivate, hr_archive])
    def test_unauthorized_attempts(self, path):
        viewer = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        assert path(client_for(viewer.user), target).status_code == 403
        assert events(target) == []

    def test_unauthorized_reactivation(self):
        viewer = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        before = len(events(target))
        assert hr_reactivate(client_for(viewer.user), target).status_code == 403
        assert len(events(target)) == before

    def test_a_higher_authority_target(self):
        actor = admin()
        boss = make_employee("Boss", "*")
        assert hr_archive(client_for(actor.user), boss).status_code == 403
        assert events(boss) == []

    def test_a_blocked_archive(self):
        actor = admin()
        head = make_employee("Head", "hr.employee.view")
        requester = make_employee("Requester", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        PurchaseRequest.objects.create(
            requisition_number=f"PR-A{next(_numbers)}", requester=requester,
            department=department, designation="Officer", contact="ext 1",
            status="PENDING_DEPARTMENT_HEAD",
        )
        assert hr_archive(client_for(actor.user), head, vacate_department_headships=True).status_code == 409
        assert events(head) == []


# =============================================================================
# The change and its record commit together
# =============================================================================


class _Boom(RuntimeError):
    pass


def _raise(*args, **kwargs):
    raise _Boom("failed")


class TestRecordAndChangeAreAtomic:
    @pytest.mark.parametrize("transition", ["deactivate", "reactivate", "archive"])
    def test_a_failing_record_rolls_the_transition_back(self, monkeypatch, transition):
        head = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        if transition == "reactivate":
            lifecycle().deactivate(head.pk)
        before_state, before_events = state(head), len(events(head))
        monkeypatch.setattr(lifecycle_events.DjangoLifecycleEventRecorder, "record", _raise)

        kwargs = {"vacate_department_headships": True} if transition == "archive" else {}
        with pytest.raises(_Boom):
            getattr(lifecycle(), transition)(head.pk, **kwargs)

        assert state(head) == before_state
        assert len(events(head)) == before_events
        assert Department.objects.get(pk=department.pk).head_id == head.pk

    @pytest.mark.parametrize("transition", ["deactivate", "reactivate", "archive"])
    def test_a_failure_after_the_record_removes_the_record_too(self, monkeypatch, transition):
        head = make_employee("Head", "hr.employee.view")
        department = Department.objects.create(name=f"Dept{next(_numbers)}", head=head)
        if transition == "reactivate":
            lifecycle().deactivate(head.pk)
        before_state, before_events = state(head), len(events(head))
        real_record = lifecycle_events.DjangoLifecycleEventRecorder.record

        def record_then_fail(self, **kwargs):
            real_record(self, **kwargs)
            raise _Boom("failed after the record was written")

        monkeypatch.setattr(lifecycle_events.DjangoLifecycleEventRecorder, "record", record_then_fail)
        kwargs = {"vacate_department_headships": True} if transition == "archive" else {}
        with pytest.raises(_Boom):
            getattr(lifecycle(), transition)(head.pk, **kwargs)

        assert state(head) == before_state
        assert len(events(head)) == before_events
        assert Department.objects.get(pk=department.pk).head_id == head.pk

    def test_a_failing_login_change_leaves_no_record(self, monkeypatch):
        target = make_employee("Target", "hr.employee.view")
        monkeypatch.setattr(identity_services, "disable_login", _raise)
        with pytest.raises(_Boom):
            lifecycle().deactivate(target.pk)
        assert state(target) == ("ACTIVE", True)
        assert events(target) == []


# =============================================================================
# History survives archival and stays unambiguous
# =============================================================================


class TestHistorySurvives:
    def test_archived_employee_keeps_their_whole_history(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        client = client_for(actor.user)
        hr_deactivate(client, target, reason="first")
        hr_reactivate(client, target, reason="second")
        hr_archive(client, target, reason="third")

        history = EmployeeLifecycleEvent.objects.filter(employee__employee_id=target.employee_id)
        assert [e.reason for e in history] == ["first", "second", "third"]
        assert {e.employee_number for e in history} == {target.employee_id}
        assert Employees.objects.get(pk=target.pk).employee_id == target.employee_id

    def test_records_name_their_actor_even_after_the_actor_is_archived(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        hr_deactivate(client_for(actor.user), target)
        lifecycle().archive(actor.pk)  # the actor's own employment closes later
        [event] = events(target)
        assert (event.actor_id, event.actor_email) == (actor.user_id, actor.email)

    def test_an_employee_with_history_cannot_be_removed_through_the_orm(self):
        target = make_employee("Target", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError), transaction.atomic():
            Employees.objects.filter(pk=target.pk).delete()
        assert len(events(target)) == 1

    def test_an_actor_with_history_cannot_be_removed_through_the_orm(self):
        actor = admin()
        target = make_employee("Target", "hr.employee.view")
        hr_deactivate(client_for(actor.user), target)
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError), transaction.atomic():
            User.objects.filter(pk=actor.user_id).delete()
        assert events(target)[0].actor_id == actor.user_id


# =============================================================================
# The model
# =============================================================================


def _event(target, **overrides):
    values = dict(
        employee=target, employee_number=target.employee_id, event_type="DEACTIVATE",
        from_status="ACTIVE", to_status="DEACTIVATED",
    )
    values.update(overrides)
    return EmployeeLifecycleEvent.objects.create(**values)


class TestModel:
    def test_minimal_record_and_defaults(self):
        target = make_employee("Target", "hr.employee.view")
        event = _event(target)
        assert (event.actor_id, event.actor_email, event.reason, event.source, event.details) == (
            None, "", "", "", {},
        )
        assert event.occurred_at is not None

    def test_target_is_required(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            EmployeeLifecycleEvent.objects.create(
                employee_id=None, employee_number="EMP1", event_type="DEACTIVATE",
                from_status="ACTIVE", to_status="DEACTIVATED",
            )

    def test_unknown_event_type_is_refused_by_the_database(self):
        target = make_employee("Target", "hr.employee.view")
        with pytest.raises(IntegrityError), transaction.atomic():
            _event(target, event_type="DELETE")

    def test_a_record_must_change_state(self):
        target = make_employee("Target", "hr.employee.view")
        with pytest.raises(IntegrityError), transaction.atomic():
            _event(target, from_status="ACTIVE", to_status="ACTIVE")


class TestAppendOnly:
    def test_a_record_cannot_be_saved_again(self):
        event = _event(make_employee("Target", "hr.employee.view"))
        event.reason = "rewritten"
        with pytest.raises(PermissionError):
            event.save()
        assert EmployeeLifecycleEvent.objects.get(pk=event.pk).reason == ""

    def test_a_record_cannot_be_deleted(self):
        event = _event(make_employee("Target", "hr.employee.view"))
        with pytest.raises(PermissionError):
            event.delete()
        assert EmployeeLifecycleEvent.objects.filter(pk=event.pk).exists()

    def test_bulk_update_is_refused(self):
        event = _event(make_employee("Target", "hr.employee.view"))
        with pytest.raises(PermissionError):
            EmployeeLifecycleEvent.objects.filter(pk=event.pk).update(reason="rewritten")
        with pytest.raises(PermissionError):
            EmployeeLifecycleEvent.objects.bulk_update([event], ["reason"])

    def test_bulk_delete_is_refused(self):
        event = _event(make_employee("Target", "hr.employee.view"))
        with pytest.raises(PermissionError):
            EmployeeLifecycleEvent.objects.filter(pk=event.pk).delete()
        assert EmployeeLifecycleEvent.objects.filter(pk=event.pk).exists()

    def test_no_route_exposes_the_records(self):
        from django.urls import get_resolver

        def names(patterns):
            for pattern in patterns:
                if hasattr(pattern, "url_patterns"):
                    yield from names(pattern.url_patterns)
                elif pattern.name:
                    yield pattern.name

        assert not [n for n in names(get_resolver().url_patterns) if "lifecycle" in n.lower()]

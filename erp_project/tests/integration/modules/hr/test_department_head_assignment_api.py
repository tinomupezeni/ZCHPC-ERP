"""
Integration tests for department-head assignment (F10-PR).

PATCH /api/v2/hr/departments/<id>/ is the existing department update
endpoint; these tests cover the newly-exposed head_id field end to end,
through the real DepartmentService/DjangoDepartmentRepository, and prove the
boundary this slice exists to close: once a department has a recorded head,
the existing (unmodified) Purchase Request department-head authorization
recognizes that employee.

Authentication uses a superuser rather than the procurement test suite's
Role/permission machinery: RBACMiddleware bypasses its coarse permission gate
for superusers (see modules.identity.infrastructure.middleware
.RBACMiddleware), and department management is not itself part of the
Purchase Request RBAC surface this repo's other tests already cover.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
)
from modules.procurement.domain.entities import PurchaseRequest
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()


def department_url(department_id):
    return f"/api/v2/hr/departments/{department_id}/"


def admin_client():
    """An authenticated client that bypasses the coarse RBAC route gate."""
    user = User.objects.create_superuser(
        email=f"hr-admin-{User.objects.count()}@zchpc.test", password="AdminPass123!"
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def make_employee(first_name, surname, suffix):
    user = User.objects.create_user(
        email=f"{first_name.lower()}.{surname.lower()}{suffix}@zchpc.test",
        password="EmployeePass123!",
    )
    return Employees.objects.create(
        user=user,
        first_name=first_name,
        surname=surname,
        email=f"{first_name.lower()}.{surname.lower()}{suffix}@zchpc.test",
        employee_id=f"EMP{suffix}",
    )


class TestAssignDepartmentHead:
    def test_assign_head_persists_and_is_readable_by_the_organizational_directory(self):
        department = Department.objects.create(name="Finance")
        head = make_employee("Hana", "Head", "1001")

        response = admin_client().patch(
            department_url(department.id), {"head_id": head.id}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["head_id"] == head.id
        assert response.data["head_name"] == "Hana Head"

        department.refresh_from_db()
        assert department.head_id == head.id

        assert (
            DjangoOrganizationalDirectory().get_department_head_id(department.id)
            == head.id
        )


class TestChangeDepartmentHead:
    def test_reassigning_points_at_the_new_head_not_the_old_one(self):
        department = Department.objects.create(name="IT")
        head_a = make_employee("Ada", "First", "1002")
        head_b = make_employee("Bo", "Second", "1003")

        client = admin_client()
        first = client.patch(
            department_url(department.id), {"head_id": head_a.id}, format="json"
        )
        assert first.status_code == status.HTTP_200_OK, first.data

        second = client.patch(
            department_url(department.id), {"head_id": head_b.id}, format="json"
        )
        assert second.status_code == status.HTTP_200_OK, second.data
        assert second.data["head_id"] == head_b.id

        department.refresh_from_db()
        assert department.head_id == head_b.id
        assert (
            DjangoOrganizationalDirectory().get_department_head_id(department.id)
            == head_b.id
        )


class TestDepartmentCanRemainWithoutAHead:
    def test_head_id_is_not_required_to_update_a_department(self):
        department = Department.objects.create(name="Research")

        response = admin_client().patch(
            department_url(department.id), {"description": "R&D team"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["description"] == "R&D team"
        assert response.data["head_id"] is None
        assert response.data["head_name"] == ""

        department.refresh_from_db()
        assert department.head_id is None

    def test_explicit_null_leaves_an_existing_head_unchanged(self):
        """
        Documented limitation: head_id=None means "not mentioned" in this
        slice, the same convention this file's `name`/`description` already
        use - there is no way to explicitly clear a recorded head yet, only
        to reassign it to a different employee (see UpdateDepartmentCommand
        and Department.update). Pinned here so that behavior doesn't
        silently change.
        """
        department = Department.objects.create(name="Legal")
        head = make_employee("Leo", "Legalis", "1004")
        client = admin_client()
        client.patch(department_url(department.id), {"head_id": head.id}, format="json")

        response = client.patch(
            department_url(department.id), {"head_id": None}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["head_id"] == head.id


class TestInvalidDepartmentHead:
    def test_nonexistent_employee_id_is_rejected(self):
        department = Department.objects.create(name="Procurement")

        response = admin_client().patch(
            department_url(department.id), {"head_id": 999999}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "INVALID_DEPARTMENT_HEAD"

        department.refresh_from_db()
        assert department.head_id is None

    def test_non_integer_head_id_is_rejected_by_the_serializer(self):
        department = Department.objects.create(name="Sales")

        response = admin_client().patch(
            department_url(department.id), {"head_id": "not-an-id"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "head_id" in response.data


class TestExistingDepartmentUpdatesStillWork:
    def test_name_and_description_update_without_head_id_in_the_payload(self):
        department = Department.objects.create(name="Old Name", description="Old")

        response = admin_client().patch(
            department_url(department.id),
            {"name": "New Name", "description": "New"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["name"] == "New Name"
        assert response.data["description"] == "New"

        department.refresh_from_db()
        assert department.name == "New Name"
        assert department.description == "New"


class TestPurchaseRequestAuthorizationBoundary:
    """
    Department.head -> DjangoOrganizationalDirectory -> Purchase Request
    department-head authorization. The Purchase Request policy itself is
    unmodified; this proves it now sees what this slice's API assigns.
    """

    def test_assigned_head_is_recognized_by_the_unmodified_authorization_policy(self):
        department = Department.objects.create(name="Engineering")
        head = make_employee("Priya", "Approver", "1005")
        requester_employee_id = 42424242  # distinct from head.id; no DB row needed

        response = admin_client().patch(
            department_url(department.id), {"head_id": head.id}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data

        policy = PurchaseRequestAuthorizationPolicy(
            directory=DjangoOrganizationalDirectory()
        )
        pending_request = PurchaseRequest.create(
            requester_id=requester_employee_id,
            requester_name="Rae Requester",
            department_id=department.id,
            department_name=department.name,
            designation="Developer",
            contact="ext 1",
        )

        head_actor = Actor(employee_id=head.id, role_name="DEPARTMENT_MANAGER")
        other_actor = Actor(employee_id=99999999, role_name="DEPARTMENT_MANAGER")

        # Does not raise: the recorded head is recognized as the authority.
        policy._require_department_authority(head_actor, pending_request)

        with pytest.raises(AuthorizationError) as exc_info:
            policy._require_department_authority(other_actor, pending_request)
        assert exc_info.value.code == "DEPARTMENT_CONTEXT_DENIED"

"""
Integration tests for the organizational directory adapter.

Department head authorization depends on the database-backed relationship
``PurchaseRequest.department -> Department.head -> Employees``, so the adapter
that reads it is exercised against the real schema rather than a stub.
"""

import pytest
from django.test import TestCase

from modules.hr.infrastructure.persistence.models import Department, Employees
from modules.procurement.application.authorization import (
    Actor,
    PurchaseRequestAuthorizationPolicy,
    PurchaseRequestPermissions as P,
)
from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.domain.entities import PurchaseRequest
from modules.procurement.domain.value_objects import RequestStatus
from modules.procurement.infrastructure.persistence.django_organizational_directory import (
    DjangoOrganizationalDirectory,
)
from shared.domain.exceptions import AuthorizationError, ValidationError


@pytest.mark.django_db
class TestDjangoOrganizationalDirectory(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name="IT Department")
        self.finance = Department.objects.create(name="Finance Department")
        self.unled = Department.objects.create(name="Facilities")

        self.it_head = Employees.objects.create(
            first_name="Mary",
            surname="Manager",
            email="mary.manager@example.com",
            department=self.it,
            employee_id="EMP001",
        )
        self.requester = Employees.objects.create(
            first_name="John",
            surname="Doe",
            email="john.doe@example.com",
            department=self.it,
            reports_to=self.it_head,
            employee_id="EMP002",
        )
        self.it_colleague = Employees.objects.create(
            first_name="Carl",
            surname="Colleague",
            email="carl.colleague@example.com",
            department=self.it,
            employee_id="EMP003",
        )
        self.finance_head = Employees.objects.create(
            first_name="Frank",
            surname="Finance",
            email="frank.finance@example.com",
            department=self.finance,
            employee_id="EMP004",
        )

        self.it.head = self.it_head
        self.it.save(update_fields=["head"])
        self.finance.head = self.finance_head
        self.finance.save(update_fields=["head"])

        self.directory = DjangoOrganizationalDirectory()
        self.policy = PurchaseRequestAuthorizationPolicy(directory=self.directory)

    def _request(self, status=RequestStatus.PENDING_DEPARTMENT_HEAD, department=None):
        department = department or self.it
        request = PurchaseRequest.create(
            requester_id=self.requester.id,
            requester_name="John Doe",
            department_id=department.id,
            department_name=department.name,
            designation="Developer",
            contact="ext 123",
        )
        request._id = 1
        request.status = status
        return request

    def _actor(self, employee, permissions=(P.DEPARTMENT_HEAD_APPROVE,)):
        return Actor(
            employee_id=employee.id,
            permissions=PermissionSet.from_list(list(permissions)),
        )

    # -- directory reads --------------------------------------------------

    def test_reads_department_head_from_hr(self):
        assert self.directory.get_department_head_id(self.it.id) == self.it_head.id
        assert (
            self.directory.get_department_head_id(self.finance.id)
            == self.finance_head.id
        )

    def test_head_is_none_when_none_is_recorded(self):
        assert self.directory.get_department_head_id(self.unled.id) is None

    def test_reads_department_from_hr(self):
        assert self.directory.get_department_id(self.requester.id) == self.it.id

    def test_unknown_ids_resolve_to_none(self):
        assert self.directory.get_department_head_id(999999) is None
        assert self.directory.get_department_id(999999) is None

    # -- authorization against the real relationship ----------------------

    def test_recorded_head_of_the_department_is_authorized(self):
        self.policy.authorize_department_head_approval(
            self._actor(self.it_head), self._request()
        )

    def test_member_of_the_department_who_is_not_the_head_is_denied(self):
        """Membership is not authority."""
        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.it_colleague), self._request()
            )

        assert ctx.exception.code == "DEPARTMENT_CONTEXT_DENIED"

    def test_head_of_another_department_is_denied(self):
        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.finance_head), self._request()
            )

        assert ctx.exception.code == "DEPARTMENT_CONTEXT_DENIED"

    def test_department_without_a_recorded_head_denies_everyone(self):
        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.it_head), self._request(department=self.unled)
            )

        assert ctx.exception.code == "DEPARTMENT_HEAD_NOT_RECORDED"

    def test_head_cannot_approve_a_request_they_raised(self):
        self.it.head = self.requester
        self.it.save(update_fields=["head"])

        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.requester), self._request()
            )

        assert ctx.exception.code == "SELF_APPROVAL_FORBIDDEN"

    def test_actor_without_the_permission_is_denied(self):
        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.it_head, permissions=[P.VIEW]), self._request()
            )

        assert ctx.exception.code == "PERMISSION_DENIED"

    def test_authorized_head_reaches_the_domain_which_still_validates_state(self):
        """Authorization passes; the aggregate still rejects the transition."""
        processed = self._request(status=RequestStatus.PROCESSED)

        self.policy.authorize_department_head_approval(
            self._actor(self.it_head), processed
        )

        with self.assertRaises(ValidationError):
            processed.approve_by_department_head(self.it_head.id)

        assert processed.status == RequestStatus.PROCESSED

    def test_head_relationship_survives_reassignment(self):
        """Authority follows the recorded head, not department membership."""
        self.it.head = self.it_colleague
        self.it.save(update_fields=["head"])

        self.policy.authorize_department_head_approval(
            self._actor(self.it_colleague), self._request()
        )

        with self.assertRaises(AuthorizationError) as ctx:
            self.policy.authorize_department_head_approval(
                self._actor(self.it_head), self._request()
            )

        assert ctx.exception.code == "DEPARTMENT_CONTEXT_DENIED"

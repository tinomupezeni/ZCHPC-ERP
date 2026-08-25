"""
Tests for DjangoEmployeeRepository's mapping between the Employee domain
entity and the normalized EmploymentDetails/EmergencyContact tables.
"""
from datetime import date

import pytest

from modules.hr.domain.entities import Employee
from modules.hr.domain.value_objects import EmergencyContact, EmploymentType
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from shared.domain.value_objects import Email, EmployeeId


@pytest.fixture
def repo():
    return DjangoEmployeeRepository()


@pytest.fixture
def department():
    from modules.hr.infrastructure.persistence.models import Department
    return Department.objects.create(name="Engineering")


@pytest.fixture
def position(department):
    from modules.hr.infrastructure.persistence.models import Position
    return Position.objects.create(title="Software Engineer", department=department)


def _new_employee(department_id=None, position_id=None, emergency_contact=None, employee_id="EMP0001"):
    return Employee(
        id=0,
        employee_id=EmployeeId(employee_id),
        first_name="Jane",
        surname="Doe",
        email=Email(f"{employee_id.lower()}@example.com"),
        department_id=department_id,
        position_id=position_id,
        employee_type=EmploymentType.FULL_TIME,
        date_joined=date(2026, 1, 15),
        contract_from=date(2026, 1, 15),
        contract_to=None,
        emergency_contact=emergency_contact or EmergencyContact(
            name="John Doe", number="0771234567", relationship="Spouse"
        ),
    )


@pytest.mark.django_db
class TestAdd:
    def test_add_creates_employment_details_row(self, repo, department, position):
        employee = _new_employee(department_id=department.id, position_id=position.id)

        repo.add(employee)

        from modules.hr.infrastructure.persistence.models import EmploymentDetails
        details = EmploymentDetails.objects.get(employee_id=employee.id)
        assert details.department_id == department.id
        assert details.position_id == position.id
        assert details.date_joined == date(2026, 1, 15)
        assert details.employee_type == "Full-time"

    def test_add_creates_emergency_contact_row(self, repo, department):
        employee = _new_employee(department_id=department.id)

        repo.add(employee)

        from modules.hr.infrastructure.persistence.models import EmergencyContact as EmergencyContactModel
        contact = EmergencyContactModel.objects.get(employee_id=employee.id)
        assert contact.name == "John Doe"
        assert contact.phone == "0771234567"
        assert contact.relationship == "Spouse"

    def test_add_does_not_construct_employees_with_employment_kwargs(self, repo, department):
        """add() must not pass department/position/employee_type/etc as
        constructor kwargs to Employees - those columns were removed in
        migration 0015 in favor of EmploymentDetails/EmergencyContact."""
        employee = _new_employee(department_id=department.id)

        repo.add(employee)

        from modules.hr.infrastructure.persistence.models import Employees
        raw = Employees.objects.get(id=employee.id)
        assert not hasattr(raw, "department_id")
        assert not hasattr(raw, "emergency_contact_name")


@pytest.mark.django_db
class TestUpdate:
    def test_update_modifies_existing_employment_details(self, repo, department, position):
        employee = _new_employee(department_id=department.id)
        repo.add(employee)

        employee.update_employment(position_id=position.id)
        repo.update(employee)

        from modules.hr.infrastructure.persistence.models import EmploymentDetails
        details = EmploymentDetails.objects.get(employee_id=employee.id)
        assert details.position_id == position.id
        assert EmploymentDetails.objects.filter(employee_id=employee.id).count() == 1

    def test_update_modifies_existing_emergency_contact(self, repo, department):
        employee = _new_employee(department_id=department.id)
        repo.add(employee)

        employee.emergency_contact = EmergencyContact(
            name="Mary Smith", number="0779999999", relationship="Sister"
        )
        repo.update(employee)

        from modules.hr.infrastructure.persistence.models import EmergencyContact as EmergencyContactModel
        contacts = EmergencyContactModel.objects.filter(employee_id=employee.id)
        assert contacts.count() == 1
        assert contacts.first().name == "Mary Smith"

    def test_update_creates_employment_details_if_missing(self, repo, department):
        """An employee added before this migration (or via a path that skipped
        EmploymentDetails) should still get one created on update, not error."""
        employee = _new_employee(department_id=department.id)
        repo.add(employee)

        from modules.hr.infrastructure.persistence.models import EmploymentDetails
        EmploymentDetails.objects.filter(employee_id=employee.id).delete()

        employee.update_employment(department_id=department.id)
        repo.update(employee)

        assert EmploymentDetails.objects.filter(employee_id=employee.id).exists()


@pytest.mark.django_db
class TestToEntity:
    def test_get_by_id_round_trips_employment_and_emergency_data(self, repo, department, position):
        employee = _new_employee(department_id=department.id, position_id=position.id)
        repo.add(employee)

        fetched = repo.get_by_id(employee.id)

        assert fetched is not None
        assert fetched.department_id == department.id
        assert fetched.position_id == position.id
        assert fetched.date_joined == date(2026, 1, 15)
        assert fetched.emergency_contact.name == "John Doe"
        assert fetched.emergency_contact.number == "0771234567"

    def test_get_by_id_handles_missing_employment_details_gracefully(self, repo, department):
        """If EmploymentDetails/EmergencyContact rows don't exist for an
        employee, _to_entity must default rather than raise."""
        employee = _new_employee(department_id=department.id)
        repo.add(employee)

        from modules.hr.infrastructure.persistence.models import (
            EmploymentDetails,
            EmergencyContact as EmergencyContactModel,
        )
        EmploymentDetails.objects.filter(employee_id=employee.id).delete()
        EmergencyContactModel.objects.filter(employee_id=employee.id).delete()

        fetched = repo.get_by_id(employee.id)

        assert fetched is not None
        assert fetched.department_id is None
        assert fetched.position_id is None
        assert fetched.employee_type == EmploymentType.FULL_TIME
        assert fetched.emergency_contact.name == ""

    def test_get_by_department_filters_via_employment_details(self, repo, department):
        from modules.hr.infrastructure.persistence.models import Department
        other_department = Department.objects.create(name="Finance")

        employee_in = _new_employee(department_id=department.id, employee_id="EMP0001")
        repo.add(employee_in)
        employee_out = _new_employee(department_id=other_department.id, employee_id="EMP0002")
        repo.add(employee_out)

        results = repo.get_by_department(department.id)

        assert [e.id for e in results] == [employee_in.id]

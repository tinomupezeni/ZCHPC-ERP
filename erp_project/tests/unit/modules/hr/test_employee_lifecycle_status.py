"""
Unit tests for the employee lifecycle model (AUD-02 Slice 2): the
EmployeeLifecycleStatus value object and how the Employee aggregate carries it.
"""

import pytest

from modules.hr.domain.entities import Employee
from modules.hr.domain.value_objects import EmployeeLifecycleStatus
from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import EmployeeId

Status = EmployeeLifecycleStatus


def make_employee(**kwargs):
    return Employee(
        id=1,
        employee_id=EmployeeId("EMP0001"),
        first_name="John",
        surname="Doe",
        **kwargs,
    )


class TestEmployeeLifecycleStatus:
    def test_exactly_three_states_exist(self):
        assert [status.value for status in Status] == ["ACTIVE", "DEACTIVATED", "ARCHIVED"]

    @pytest.mark.parametrize("value", ["ACTIVE", "DEACTIVATED", "ARCHIVED"])
    def test_stored_values_convert(self, value):
        assert Status.from_string(value).value == value

    @pytest.mark.parametrize("value", ["", "active", "DELETED", "INACTIVE", None])
    def test_anything_else_is_rejected(self, value):
        with pytest.raises(ValueError):
            Status.from_string(value)


class TestEmployeeCarriesOneLifecycleState:
    def test_new_employee_is_active(self):
        employee = make_employee()
        assert employee.lifecycle_status is Status.ACTIVE

    @pytest.mark.parametrize(
        "status,is_active,is_deactivated,is_archived",
        [
            (Status.ACTIVE, True, False, False),
            (Status.DEACTIVATED, False, True, False),
            (Status.ARCHIVED, False, False, True),
        ],
    )
    def test_each_state_is_exclusive(self, status, is_active, is_deactivated, is_archived):
        employee = make_employee(lifecycle_status=status)
        assert employee.is_active is is_active
        assert employee.is_deactivated is is_deactivated
        assert employee.is_archived is is_archived

    def test_stored_string_is_accepted(self):
        assert make_employee(lifecycle_status="ARCHIVED").lifecycle_status is Status.ARCHIVED

    def test_invalid_state_is_rejected(self):
        with pytest.raises(ValueError):
            make_employee(lifecycle_status="DELETED")

    def test_is_active_is_derived_and_cannot_be_set(self):
        employee = make_employee()
        with pytest.raises(AttributeError):
            employee.is_active = False
        assert employee.lifecycle_status is Status.ACTIVE

    def test_is_active_is_no_longer_a_constructor_argument(self):
        with pytest.raises(TypeError):
            make_employee(is_active=False)


class TestExistingTransitionsUseTheLifecycleState:
    def test_deactivate_moves_to_deactivated(self):
        employee = make_employee()
        employee.deactivate()
        assert employee.lifecycle_status is Status.DEACTIVATED

    def test_reactivate_moves_back_to_active(self):
        employee = make_employee(lifecycle_status=Status.DEACTIVATED)
        employee.reactivate()
        assert employee.lifecycle_status is Status.ACTIVE

    @pytest.mark.parametrize("transition", ["deactivate", "reactivate"])
    def test_archived_is_not_reopened_by_either(self, transition):
        employee = make_employee(lifecycle_status=Status.ARCHIVED)
        with pytest.raises(ValidationError) as exc:
            getattr(employee, transition)()
        assert exc.value.code == "EMPLOYEE_ARCHIVED"
        assert employee.lifecycle_status is Status.ARCHIVED

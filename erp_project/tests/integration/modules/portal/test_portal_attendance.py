"""
Portal attendance: status, history and summary after a clock-in.

AttendanceRecord stores time_in/time_out as TimeField, but the portal treats
them as datetimes (DTO, ClockStatus.worked_hours, DateTimeField serializers).
Once an employee had clocked in, status and history returned 500
("'datetime.time' object has no attribute 'astimezone'"), clock-out failed the
same way, and the summary failed on time - time. Found in the local check of
the Attendance display fix (2026-10-13).

The provider now reads each stored time as a UTC datetime on the record's date.
"""

from datetime import date, datetime, time, timezone
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.hr.infrastructure.persistence.models import Employees, Role

pytestmark = pytest.mark.django_db

User = get_user_model()

PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
STATUS_URL = "/api/v2/portal/attendance/status/"
CLOCK_URL = "/api/v2/portal/attendance/clock/"
HISTORY_URL = "/api/v2/portal/attendance/history/"
SUMMARY_URL = "/api/v2/portal/attendance/summary/"
PASSWORD = "Str0ng-Initial-Passw0rd"

_numbers = count(74001)


def make_employee(label):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password=PASSWORD)
    role = Role.objects.create(name=f"ATTENDANCE_{n}", display_name=label, permissions=["portal.*"])
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}", role=role,
    )


def portal_client(employee):
    response = APIClient().post(
        PORTAL_LOGIN_URL,
        {"ec_number": employee.employee_id, "password": PASSWORD},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


class TestAfterClockIn:
    def test_clock_in_then_status_history_and_summary_load(self):
        client = portal_client(make_employee("Chipo"))

        assert client.post(CLOCK_URL, {}, format="json").status_code == status.HTTP_200_OK

        status_response = client.get(STATUS_URL)
        assert status_response.status_code == status.HTTP_200_OK
        assert status_response.data["is_clocked_in"] is True
        assert status_response.data["clock_in_time"] is not None

        history = client.get(HISTORY_URL)
        assert history.status_code == status.HTTP_200_OK
        assert len(history.data) == 1
        assert history.data[0]["time_in"] is not None
        assert history.data[0]["time_out"] is None

        assert client.get(SUMMARY_URL).status_code == status.HTTP_200_OK

    def test_clock_out_after_clock_in(self):
        client = portal_client(make_employee("Tanaka"))
        client.post(CLOCK_URL, {}, format="json")

        response = client.post(CLOCK_URL, {}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["record"]["time_out"] is not None
        assert client.get(STATUS_URL).data["is_clocked_in"] is False


class TestStoredTimes:
    def test_times_are_sent_as_utc_datetimes_on_the_record_date(self):
        employee = make_employee("Rudo")
        today = date.today()
        AttendanceRecord.objects.create(
            employee=employee, date=today, time_in=time(6, 5), time_out=time(14, 35),
        )
        client = portal_client(employee)

        status_data = client.get(STATUS_URL).data
        record = client.get(HISTORY_URL).data[0]

        expected_in = datetime.combine(today, time(6, 5), tzinfo=timezone.utc)
        expected_out = datetime.combine(today, time(14, 35), tzinfo=timezone.utc)
        assert datetime.fromisoformat(record["time_in"].replace("Z", "+00:00")) == expected_in
        assert datetime.fromisoformat(record["time_out"].replace("Z", "+00:00")) == expected_out
        assert status_data["is_clocked_in"] is False
        assert status_data["worked_hours"] == pytest.approx(8.5)

    def test_summary_adds_up_the_hours(self):
        employee = make_employee("Nyasha")
        today = date.today()
        AttendanceRecord.objects.create(
            employee=employee, date=today, time_in=time(7, 0), time_out=time(15, 30),
        )

        summary = portal_client(employee).get(SUMMARY_URL).data

        assert summary["present_days"] == 1
        assert summary["total_hours"] == pytest.approx(8.5)

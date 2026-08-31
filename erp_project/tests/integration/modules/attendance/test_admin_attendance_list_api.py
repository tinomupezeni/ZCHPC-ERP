"""
Integration tests for the admin/HR attendance listing endpoint
(GET /api/v2/attendance/all/), which supports department/employee/date-range filters.
"""
from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.integration

URL = "/api/v2/attendance/all/"


@pytest.mark.django_db
class TestAdminAttendanceListAPI:
    def test_requires_authentication(self):
        from rest_framework.test import APIClient

        response = APIClient().get(URL)
        assert response.status_code in (401, 403)

    def test_non_admin_staff_is_forbidden(self, staff_client, employees_with_attendance):
        response = staff_client.get(URL)
        assert response.status_code == 403

    def test_admin_lists_all_employees_attendance(self, admin_client, employees_with_attendance):
        response = admin_client.get(URL)
        assert response.status_code == 200
        assert response.data["count"] == 3

        names = {r["employee_name"] for r in response.data["results"]}
        assert names == {"Alice IT", "Bob Apps"}

    def test_filter_by_department(self, admin_client, employees_with_attendance, departments):
        response = admin_client.get(URL, {"department_id": departments["applications"].id})
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["employee_name"] == "Bob Apps"
        assert response.data["results"][0]["department_name"] == "Applications"

    def test_filter_by_date_range(self, admin_client, employees_with_attendance):
        today = date.today()
        response = admin_client.get(
            URL,
            {"start_date": today.isoformat(), "end_date": today.isoformat()},
        )
        assert response.status_code == 200
        assert response.data["count"] == 2
        for record in response.data["results"]:
            assert record["record_date"] == today.isoformat()

    def test_filter_by_employee(self, admin_client, employees_with_attendance):
        alice = employees_with_attendance["it"]
        response = admin_client.get(URL, {"employee_id": alice.id})
        assert response.status_code == 200
        assert response.data["count"] == 2
        assert all(r["employee_name"] == "Alice IT" for r in response.data["results"])

    def test_combined_department_and_date_filters_exclude_out_of_range(
        self, admin_client, employees_with_attendance, departments
    ):
        old_date = (date.today() - timedelta(days=10)).isoformat()
        response = admin_client.get(
            URL,
            {"department_id": departments["it"].id, "start_date": old_date, "end_date": old_date},
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["record_date"] == old_date

"""
Regression test: the leave request lifecycle (submit -> admin review ->
approve/reject/cancel) must actually work end to end.

Every mutating leave action (submit, approve, reject, cancel) raised a
domain event constructed with keyword arguments that didn't match the
event dataclass's fields (e.g. LeaveRequested(requested_at=...) when the
event has no such field, LeaveRequestService calling
self._approval_policy.can_approve(reviewer_id=...) when the method takes
approver_id, and can_reject() not existing on the policy at all) - so
every single one of these endpoints 400'd unconditionally. None of it had
ever been exercised by a test before.

Also covers: an HR admin who isn't linked to their own Employees record
(e.g. a superuser test/automation account) must still be able to see and
review leave requests - LeaveRequestReviewView used to hard-400 for any
caller without an employee link, including admins.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestLeaveRequestLifecycle:
    def _init_balance(self, employee_client, employee_id):
        response = employee_client.post(
            f"/api/v2/leave/balances/initialize/{employee_id}/", {}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_submit_admin_list_approve_by_unlinked_admin(
        self, employee_client, admin_client, leave_type
    ):
        self._init_balance(employee_client, employee_client.employee.id)

        submit = employee_client.post(
            "/api/v2/leave/requests/",
            {
                "leave_type_id": leave_type.id,
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
                "reason": "Regression test leave",
            },
            format="json",
        )
        assert submit.status_code == status.HTTP_201_CREATED, submit.data
        request_id = submit.data["id"]

        # Own-employee listing still works.
        own_list = employee_client.get("/api/v2/leave/requests/")
        assert own_list.status_code == status.HTTP_200_OK
        assert any(r["id"] == request_id for r in own_list.data)

        # Admin-wide listing sees it too, with the frontend's expected field names.
        admin_list = admin_client.get("/api/v2/leave/requests/all/")
        assert admin_list.status_code == status.HTTP_200_OK
        row = next(r for r in admin_list.data if r["id"] == request_id)
        assert row["employee_name"] == "Test Employee"
        assert row["leave_type_name"] == leave_type.name
        assert row["number_of_days"] == 3
        assert row["status"] == "Pending"

        # A superuser with no linked Employees record can still approve.
        approve = admin_client.post(
            f"/api/v2/leave/requests/{request_id}/review/", {"approved": True}, format="json"
        )
        assert approve.status_code == status.HTTP_200_OK, approve.data
        assert approve.data["status"] == "Approved"

    def test_admin_reject_with_reason(self, employee_client, admin_client, leave_type):
        self._init_balance(employee_client, employee_client.employee.id)

        submit = employee_client.post(
            "/api/v2/leave/requests/",
            {
                "leave_type_id": leave_type.id,
                "start_date": "2026-10-05",
                "end_date": "2026-10-05",
                "reason": "Reject me",
            },
            format="json",
        )
        request_id = submit.data["id"]

        reject = admin_client.post(
            f"/api/v2/leave/requests/{request_id}/review/",
            {"approved": False, "rejection_reason": "No coverage"},
            format="json",
        )
        assert reject.status_code == status.HTTP_200_OK, reject.data
        assert reject.data["status"] == "Rejected"

    def test_employee_can_cancel_own_request(self, employee_client, leave_type):
        self._init_balance(employee_client, employee_client.employee.id)

        submit = employee_client.post(
            "/api/v2/leave/requests/",
            {
                "leave_type_id": leave_type.id,
                "start_date": "2026-11-01",
                "end_date": "2026-11-01",
                "reason": "Cancel me",
            },
            format="json",
        )
        request_id = submit.data["id"]

        cancel = employee_client.post(f"/api/v2/leave/requests/{request_id}/cancel/", {}, format="json")
        assert cancel.status_code == status.HTTP_200_OK, cancel.data
        assert cancel.data["status"] == "Cancelled"

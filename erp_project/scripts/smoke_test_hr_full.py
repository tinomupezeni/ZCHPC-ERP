#!/usr/bin/env python3
"""
Full smoke test for the HR module - one HTTP session, one pass over every
admin tab: Employees, Attendance, Recruitment, Training & Development,
Reports, Company Calendar, Leave Applications.

Exercises the real endpoints end-to-end against a running deployment.
Where a tab has no working backend yet, the script says so explicitly
instead of silently skipping it or pretending it passed.

Usage:
    python scripts/smoke_test_hr_full.py \
        --base-url http://10.50.14.12:8000/api/v2/ \
        --email automation@zchpc.ac.zw --password '...'

    Or set SMOKE_BASE_URL / SMOKE_EMAIL / SMOKE_PASSWORD env vars.

The login user should be a superuser (e.g. the automation account from
`manage.py create_test_account`) - several admin endpoints below
(attendance/leave/recruitment) require HR/Admin/Manager-level access.

Exits 0 if every applicable check passes, 1 on the first hard failure.
Known-incomplete areas (Training & Development, most Reports types) are
printed as SKIPPED, not counted as failures.
"""
import argparse
import os
import sys
from datetime import date, timedelta

import requests

sys.path.insert(0, os.path.dirname(__file__))
from smoke_test_employees import EmployeeCrudSmokeTest, SmokeTestFailure, step  # noqa: E402


class HrFullSmokeTest:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip("/") + "/"
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.skipped = []

    def run(self) -> None:
        self.login()

        print("\n=== HR Employees ===")
        employees = EmployeeCrudSmokeTest.__new__(EmployeeCrudSmokeTest)
        employees.base_url = self.base_url
        employees.session = self.session
        employees.employee_id = None
        employees.create_employee()
        employees.get_employee()
        employees.list_employees()
        employees.update_employee()
        employees.deactivate_employee()

        print("\n=== Attendance ===")
        self.attendance_admin_list()

        print("\n=== Recruitment ===")
        self.recruitment_job_lifecycle()

        print("\n=== Training & Development ===")
        self.skip(
            "Training & Development",
            "frontend Server.tsx methods are hardcoded mock stubs - no backend "
            "module exists yet. Nothing to smoke test.",
        )

        print("\n=== Reports ===")
        self.reports()

        print("\n=== Company Calendar ===")
        self.company_calendar_lifecycle()

        print("\n=== Leave Applications ===")
        self.leave_applications()

        print("\nAll applicable checks passed.")
        if self.skipped:
            print("\nSkipped (known gaps, not failures):")
            for name, reason in self.skipped:
                print(f"  - {name}: {reason}")

    # -- Auth -----------------------------------------------------------

    @step("Logging in")
    def login(self):
        resp = self.session.post(
            self._url("auth/token/"),
            json={"email": self.email, "password": self.password},
            timeout=10,
        )
        self._expect(resp, 200, "login")
        token = resp.json().get("access")
        if not token:
            raise SmokeTestFailure("Login response had no 'access' token")
        self.session.headers["Authorization"] = f"Bearer {token}"

    # -- Attendance -------------------------------------------------------

    @step("Listing attendance records (admin/HR view, across all employees)")
    def attendance_admin_list(self):
        resp = self.session.get(self._url("attendance/all/"), timeout=10)
        self._expect(resp, 200, "admin attendance list")
        data = resp.json()
        if "results" not in data or "count" not in data:
            raise SmokeTestFailure(f"Unexpected admin attendance list shape: {list(data.keys())}")

    # -- Recruitment ------------------------------------------------------

    @step("Creating, publishing, listing, and closing a job posting")
    def recruitment_job_lifecycle(self):
        department_id = self._get_or_create_department()

        payload = {
            "title": f"Smoke Test Role {date.today().isoformat()}",
            "department_id": department_id,
            "description": "Created by the HR module smoke test.",
            "location": "Harare",
            "is_internal": False,
            "status": "Draft",
        }
        resp = self.session.post(self._url("recruitment/jobs/"), json=payload, timeout=10)
        self._expect(resp, 201, "create job")
        job_id = resp.json()["id"]

        resp = self.session.post(self._url(f"recruitment/jobs/{job_id}/publish/"), timeout=10)
        self._expect(resp, 200, "publish job")
        if resp.json().get("status") != "Open":
            raise SmokeTestFailure(f"Published job should be Open: {resp.json()}")

        resp = self.session.get(self._url("recruitment/jobs/"), timeout=10)
        self._expect(resp, 200, "list jobs")
        ids = {j["id"] for j in resp.json()}
        if job_id not in ids:
            raise SmokeTestFailure(f"Published job id={job_id} not in job list")

        # Also visible on the public careers listing (internal or not).
        resp = self.session.get(self._url("recruitment/public/jobs/"), timeout=10)
        self._expect(resp, 200, "public job list")
        public_ids = {j["id"] for j in resp.json()}
        if job_id not in public_ids:
            raise SmokeTestFailure(f"Open job id={job_id} should appear on the public careers page")

        resp = self.session.post(self._url(f"recruitment/jobs/{job_id}/close/"), timeout=10)
        self._expect(resp, 200, "close job")
        if resp.json().get("status") != "Closed":
            raise SmokeTestFailure(f"Closed job should report status Closed: {resp.json()}")

    def _get_or_create_department(self) -> int:
        resp = self.session.get(self._url("hr/departments/"), timeout=10)
        self._expect(resp, 200, "list departments")
        departments = resp.json()
        if departments:
            return departments[0]["id"]

        resp = self.session.post(
            self._url("hr/departments/"),
            json={"name": "Smoke Test Department", "description": "Created by smoke test"},
            timeout=10,
        )
        self._expect(resp, 201, "create department")
        return resp.json()["id"]

    # -- Reports ------------------------------------------------------------

    @step("Checking Reports endpoints (payroll summary + employees report)")
    def reports(self):
        period = date.today().strftime("%Y-%m")
        resp = self.session.get(self._url(f"payroll/summary/?period={period}"), timeout=10)
        if resp.status_code == 404:
            # No payslips processed for the current period yet - legitimate,
            # not a bug. Backend field names are still worth spot-checking
            # via a period that's more likely to have data, so don't hard-fail.
            pass
        elif resp.status_code == 200:
            data = resp.json()
            for field in ("total_gross_usd", "total_net_usd", "total_paye_usd", "total_nssa_usd"):
                if field not in data:
                    raise SmokeTestFailure(f"payroll summary missing expected field {field!r}: {data}")
        else:
            raise SmokeTestFailure(f"payroll summary: unexpected status {resp.status_code}: {resp.text[:300]}")

        resp = self.session.get(self._url("hr/employees/"), timeout=10)
        self._expect(resp, 200, "employees report data")

        self.skip(
            "Reports (9 of 13 report types)",
            "necPension, zimdef, medicalAid, bonus, vehicleBenefit, overtime, "
            "promotion, loan, terminalBenefits have no backend endpoint - the "
            "frontend silently returns an empty table for these, by design "
            "(see reports.services.tsx REPORT_ENDPOINTS).",
        )

    # -- Company Calendar -----------------------------------------------------

    @step("Creating, listing, updating, and deleting a calendar event")
    def company_calendar_lifecycle(self):
        today = date.today()
        payload = {
            "title": "Smoke Test Event",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=1)).isoformat(),
            "event_type": "Other",
        }
        resp = self.session.post(self._url("hr/events/"), json=payload, timeout=10)
        self._expect(resp, (200, 201), "create event")
        event_id = resp.json()["id"]

        resp = self.session.get(self._url("hr/events/"), timeout=10)
        self._expect(resp, 200, "list events")
        ids = {e["id"] for e in resp.json()}
        if event_id not in ids:
            raise SmokeTestFailure(f"Created event id={event_id} not in event list")

        resp = self.session.patch(
            self._url(f"hr/events/{event_id}/"), json={"title": "Smoke Test Event (updated)"}, timeout=10
        )
        self._expect(resp, 200, "update event")

        resp = self.session.delete(self._url(f"hr/events/{event_id}/"), timeout=10)
        self._expect(resp, (200, 204), "delete event")

        resp = self.session.get(self._url(f"hr/events/{event_id}/"), timeout=10)
        self._expect(resp, 404, "re-fetch deleted event")

    # -- Leave Applications ---------------------------------------------------

    @step("Checking Leave Applications endpoints (types + admin-wide listing)")
    def leave_applications(self):
        resp = self.session.get(self._url("leave/types/"), timeout=10)
        self._expect(resp, 200, "list leave types")
        if not resp.json():
            raise SmokeTestFailure(
                "No leave types exist - run `manage.py seed_test_employees` first "
                "(it seeds Annual/Sick/Compassionate/Maternity/Paternity leave types)."
            )

        resp = self.session.get(self._url("leave/requests/all/"), timeout=10)
        self._expect(resp, 200, "admin-wide leave request listing")
        for row in resp.json()[:1]:
            for field in ("employee_name", "leave_type_name", "number_of_days", "status"):
                if field not in row:
                    raise SmokeTestFailure(f"admin leave request row missing {field!r}: {row}")

        self.skip(
            "Leave Applications (submit -> approve/reject -> cancel)",
            "the full lifecycle needs a second, employee-linked login (submitting "
            "leave is self-service, scoped to the caller's own Employees record) - "
            "covered instead by tests/integration/modules/leave/test_leave_lifecycle.py.",
        )

    # -- Helpers ------------------------------------------------------------

    def skip(self, name: str, reason: str) -> None:
        print(f"-> {name}: SKIPPED ({reason})")
        self.skipped.append((name, reason))

    def _url(self, path: str) -> str:
        return self.base_url + path

    @staticmethod
    def _expect(resp: "requests.Response", expected, step_name: str) -> None:
        expected_codes = (expected,) if isinstance(expected, int) else expected
        if resp.status_code not in expected_codes:
            raise SmokeTestFailure(
                f"{step_name}: expected status {expected_codes}, got {resp.status_code}: {resp.text[:500]}"
            )


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000/api/v2/"),
        help="API base URL, e.g. http://10.50.14.12:8000/api/v2/ (default: %(default)s, or $SMOKE_BASE_URL)",
    )
    parser.add_argument("--email", default=os.environ.get("SMOKE_EMAIL"), help="Login email (or $SMOKE_EMAIL)")
    parser.add_argument("--password", default=os.environ.get("SMOKE_PASSWORD"), help="Login password (or $SMOKE_PASSWORD)")
    args = parser.parse_args()
    if not args.email or not args.password:
        parser.error("--email/--password are required (or set SMOKE_EMAIL/SMOKE_PASSWORD)")
    return args


def main():
    args = parse_args()
    print(f"Running full HR module smoke test against {args.base_url}")
    test = HrFullSmokeTest(args.base_url, args.email, args.password)
    try:
        test.run()
    except SmokeTestFailure as exc:
        print("FAILED")
        print(f"\n{exc}")
        sys.exit(1)
    except requests.RequestException as exc:
        print("FAILED")
        print(f"\nRequest error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

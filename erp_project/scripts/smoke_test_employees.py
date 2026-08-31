#!/usr/bin/env python3
"""
Smoke test for the HR Employees CRUD API.

Exercises the real HTTP endpoints end-to-end - login, create, read, list,
update, deactivate - against a running deployment. Use this to quickly
verify employee CRUD is actually working after a deploy, without writing
or running a full test suite.

Usage:
    python scripts/smoke_test_employees.py \
        --base-url http://10.50.14.12:8000/api/v2/ \
        --email admin@zchpc.ac.zw --password '...'

    Or set SMOKE_BASE_URL / SMOKE_EMAIL / SMOKE_PASSWORD env vars instead
    of passing flags (handy for not leaving a password in shell history).

The login user must have permission to create/update/deactivate employees
(a superuser, or HR/ADMIN role).

Exits 0 if every step passes, 1 on the first failure.
"""
import argparse
import os
import sys
from datetime import date

import requests


class SmokeTestFailure(Exception):
    """Raised when a step doesn't behave as expected."""


def step(description):
    """Print a step header before running it; leaves the line open so the
    caller's OK/FAILED prints right after it."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            print(f"-> {description} ...", end=" ", flush=True)
            result = fn(*args, **kwargs)
            print("OK")
            return result
        return wrapper
    return decorator


class EmployeeCrudSmokeTest:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip("/") + "/"
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.employee_id = None

    def run(self) -> None:
        self.login()
        self.create_employee()
        self.get_employee()
        self.list_employees()
        self.update_employee()
        self.deactivate_employee()
        print(
            f"\nAll checks passed. Test employee id={self.employee_id} was "
            f"created then deactivated (soft delete - there's no hard-delete "
            f"endpoint) - safe to leave, or clean up manually."
        )

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

    @step("Creating employee")
    def create_employee(self):
        today = date.today()
        dob = today.replace(year=today.year - 30)
        suffix = today.strftime("%Y%m%d%H%M%S")
        payload = {
            "first_name": "Smoke",
            "surname": "Test",
            "email": f"smoketest+{suffix}@zchpc.ac.zw",
            "phone": "0771234567",
            "date_of_birth": dob.isoformat(),
            "gender": "Male",
            "employee_type": "Full-time",
            "usd_salary": "1000.00",
            "zig_salary": "20000.00",
            "bank_name": "CBZ",
            "bank_account": "0000111122",
            "nssa_number": "SMOKE-NSSA",
        }
        resp = self.session.post(self._url("hr/employees/"), json=payload, timeout=10)
        self._expect(resp, 201, "create employee")
        data = resp.json()
        self.employee_id = data["id"]
        if data.get("first_name") != "Smoke" or data.get("surname") != "Test":
            raise SmokeTestFailure(f"Created employee has unexpected name: {data}")

    @step("Reading employee back")
    def get_employee(self):
        resp = self.session.get(self._url(f"hr/employees/{self.employee_id}/"), timeout=10)
        self._expect(resp, 200, "get employee")
        data = resp.json()
        if float(data.get("usd_salary") or 0) != 1000.00:
            raise SmokeTestFailure(f"usd_salary did not round-trip: {data.get('usd_salary')!r}")
        if float(data.get("zig_salary") or 0) != 20000.00:
            raise SmokeTestFailure(f"zig_salary did not round-trip: {data.get('zig_salary')!r}")
        if data.get("is_active") is not True:
            raise SmokeTestFailure(f"New employee should be active: {data}")

    @step("Listing employees")
    def list_employees(self):
        resp = self.session.get(self._url("hr/employees/"), timeout=10)
        self._expect(resp, 200, "list employees")
        data = resp.json()
        ids = {row.get("id") for row in data} if isinstance(data, list) else set()
        if self.employee_id not in ids:
            raise SmokeTestFailure(
                f"Created employee id={self.employee_id} not found in list of {len(ids)} employees"
            )

    @step("Updating employee")
    def update_employee(self):
        resp = self.session.patch(
            self._url(f"hr/employees/{self.employee_id}/"),
            json={"usd_salary": "1500.00", "phone": "0779999999"},
            timeout=10,
        )
        self._expect(resp, 200, "update employee")

        resp = self.session.get(self._url(f"hr/employees/{self.employee_id}/"), timeout=10)
        self._expect(resp, 200, "re-fetch employee after update")
        data = resp.json()
        if float(data.get("usd_salary") or 0) != 1500.00:
            raise SmokeTestFailure(f"usd_salary update did not persist: {data.get('usd_salary')!r}")
        if data.get("phone") != "0779999999":
            raise SmokeTestFailure(f"phone update did not persist: {data.get('phone')!r}")

    @step("Deactivating employee")
    def deactivate_employee(self):
        resp = self.session.delete(self._url(f"hr/employees/{self.employee_id}/"), timeout=10)
        self._expect(resp, (200, 204), "deactivate employee")

        resp = self.session.get(self._url(f"hr/employees/{self.employee_id}/"), timeout=10)
        self._expect(resp, 200, "re-fetch employee after deactivate")
        if resp.json().get("is_active") is not False:
            raise SmokeTestFailure("Employee should be inactive after DELETE")

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
    print(f"Running employee CRUD smoke test against {args.base_url}\n")
    test = EmployeeCrudSmokeTest(args.base_url, args.email, args.password)
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

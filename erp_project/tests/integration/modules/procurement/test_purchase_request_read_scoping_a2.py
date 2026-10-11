"""
A2 (PLAN assumption A-2): purchase request read-by-id is scoped.

GET /requests/<id>/ and GET /requests/<id>/actions/ disclose a request only to:
- the requester and admins;
- for a DRAFT, the requester only;
- otherwise a reviewer the request has reached: one holding the capability of
  a stage at or before the furthest stage reached. The department head stage
  also needs Department.head of the request's department.

Before A2 any holder of ``procurement.purchase_request.view`` could read any
request by id, drafts included.
"""

import pytest

from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from modules.procurement.infrastructure.persistence.models import PurchaseRequestDecision

pytestmark = pytest.mark.django_db

ENDPOINTS = ["", "actions/"]


@pytest.fixture
def get(client_for, api_url):
    def _get(employee, record, endpoint=""):
        return client_for(employee).get(f"{api_url}{record.id}/{endpoint}")

    return _get


@pytest.fixture
def staff(make_employee):
    """Another ordinary staff member: holds view, reviews nothing."""
    return make_employee("Sam Staff", [P.CREATE, P.VIEW, P.SUBMIT])


@pytest.fixture
def reviewers(department_head, other_department_head, accountant, general_manager, director,
              procurement_officer):
    return {
        "department_head": department_head,
        "other_department_head": other_department_head,
        "accountant": accountant,
        "general_manager": general_manager,
        "director": director,
        "procurement_officer": procurement_officer,
    }


def reject_at(record, stage, actor):
    PurchaseRequestDecision.objects.create(
        purchase_request=record, stage=stage, decision="REJECTED", actor=actor, reason="No budget",
    )


@pytest.mark.parametrize("endpoint", ENDPOINTS)
class TestDraft:
    def test_the_requester_reads_their_draft(self, get, requester, make_request_record, endpoint):
        assert get(requester, make_request_record(requester), endpoint).status_code == 200

    def test_requester_cannot_read_another_users_draft(self, get, requester, staff, make_request_record,
                                                       endpoint):
        response = get(staff, make_request_record(requester), endpoint)

        assert response.status_code == 403

    def test_no_reviewer_reads_a_draft(self, get, requester, reviewers, make_request_record, endpoint):
        record = make_request_record(requester)
        for name, reviewer in reviewers.items():
            assert get(reviewer, record, endpoint).status_code == 403, name

    def test_admin_reads_a_draft(self, get, requester, make_employee, make_request_record, endpoint):
        admin = make_employee("Ada Admin", ["*"])
        admin.user.is_superuser = True
        admin.user.save(update_fields=["is_superuser"])
        assert get(admin, make_request_record(requester), endpoint).status_code == 200


# status -> the reviewers who may read a request in it (the rest are refused)
READERS = {
    "PENDING_DEPARTMENT_HEAD": {"department_head"},
    "PENDING_ACCOUNTS": {"department_head", "accountant"},
    "PENDING_GM": {"department_head", "accountant", "general_manager"},
    "PENDING_DIRECTOR": {"department_head", "accountant", "general_manager", "director"},
    "PENDING_PROCUREMENT": {"department_head", "accountant", "general_manager", "director",
                            "procurement_officer"},
    "PROCESSED": {"department_head", "accountant", "general_manager", "director", "procurement_officer"},
}


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("status", list(READERS))
def test_reviewers_read_a_request_once_it_has_reached_their_stage(
    get, requester, staff, reviewers, make_request_record, status, endpoint
):
    record = make_request_record(requester, status=status)

    assert get(requester, record, endpoint).status_code == 200
    assert get(staff, record, endpoint).status_code == 403
    for name, reviewer in reviewers.items():
        expected = 200 if name in READERS[status] else 403
        assert get(reviewer, record, endpoint).status_code == expected, name


@pytest.mark.parametrize(
    "stage,readers",
    [
        ("DEPARTMENT_HEAD", {"department_head"}),
        ("ACCOUNTS", {"department_head", "accountant"}),
        ("DIRECTOR", {"department_head", "accountant", "general_manager", "director"}),
    ],
)
def test_a_rejected_request_is_readable_up_to_the_stage_that_rejected_it(
    get, requester, staff, reviewers, make_request_record, stage, readers
):
    record = make_request_record(requester, status="REJECTED")
    reject_at(record, stage, reviewers["department_head"])

    assert get(requester, record).status_code == 200
    assert get(staff, record).status_code == 403
    for name, reviewer in reviewers.items():
        expected = 200 if name in readers else 403
        assert get(reviewer, record).status_code == expected, name


def test_the_head_of_another_department_is_refused_at_every_stage(get, requester, reviewers,
                                                                    make_request_record):
    for status in READERS:
        record = make_request_record(requester, status=status)
        assert get(reviewers["other_department_head"], record).status_code == 403, status


def test_view_alone_is_not_enough_for_someone_elses_submitted_request(get, requester, staff,
                                                                     make_request_record):
    record = make_request_record(requester, status="PENDING_ACCOUNTS")
    response = get(staff, record, "actions/")

    assert response.status_code == 403

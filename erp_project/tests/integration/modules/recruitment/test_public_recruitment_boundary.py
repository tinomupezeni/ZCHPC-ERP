"""
REM-04: the public careers boundary.

Public by design: open jobs (internal ones too), anonymous application and
status lookup. These tests pin what that surface may disclose and change:

- jobs go out through an explicit allowlist (salary yes, applicant count no);
- check-application answers only ``has_applied``;
- an anonymous submission never rewrites an existing Candidate record, and a
  national ID / email collision is refused without naming anyone;
- the same applicant resubmitting for the same job updates that application;
- status lookup does not distinguish unknown IDs from IDs with no applications;
- a decided (Hired/Rejected) application cannot be changed anonymously;
- a new submission can never overwrite an existing row through an ID
  collision - primary keys are database-assigned;
- the anonymous endpoints are rate limited, on both the recruitment and the
  portal routes, and a client-supplied X-Forwarded-For cannot reset the limit;
- resumes are stored under unguessable names and never appear in responses.
"""
import re

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department
from modules.recruitment.api import throttles
from modules.recruitment.infrastructure.persistence.models import Candidate, Job, JobApplication

pytestmark = pytest.mark.integration

PUBLIC = "/api/v2/recruitment/public"
PORTAL = "/api/v2/portal/public"

PUBLIC_JOB_FIELDS = {
    "id", "title", "department_id", "department_name", "position_id", "position_title",
    "status", "location", "reports_to", "salary_usd_min", "salary_usd_max",
    "salary_zig_min", "salary_zig_max", "is_internal", "description", "responsibilities",
    "qualifications", "competencies", "application_process", "contact_email", "posted_date",
}
RECEIPT_FIELDS = {"id", "job_id", "job_title", "status", "applied_at", "updated_at"}
STATUS_FIELDS = {"job_id", "job_title", "status", "applied_at"}

VICTIM_NID = "63-111111A11"
VICTIM_EMAIL = "victim@example.com"


def resume(name="resume.pdf", body=b"%PDF-1.4 resume"):
    return SimpleUploadedFile(name, body, content_type="application/pdf")


def apply(client=None, **overrides):
    payload = {
        "id_number": VICTIM_NID,
        "first_name": "Victim",
        "last_name": "Person",
        "email": VICTIM_EMAIL,
        "phone": "0770000000",
        "address": "1 Real Street",
        "qualifications": "BSc",
        "experience": "5 years",
        "cover_letter": "Original letter",
        "resume": resume(),
    }
    payload.update(overrides)
    return (client or APIClient()).post(f"{PUBLIC}/jobs/apply/", payload, format="multipart")


@pytest.fixture
def jobs(db):
    department = Department.objects.create(name="Careers Dept", description="")

    def make(title, status="Open", is_internal=False, **extra):
        return Job.objects.create(
            title=title, status=status, is_internal=is_internal, department=department, **extra
        )

    return {
        "external": make("External Open", salary_usd_min=1000, salary_usd_max=2000,
                         notes="INTERNAL HR NOTE"),
        "internal": make("Internal Open", is_internal=True),
        "draft": make("Draft Role", status="Draft"),
        "pending": make("Pending Role", status="Pending"),
        "closed": make("Closed Role", status="Closed"),
    }


@pytest.fixture
def victim(jobs):
    """An existing candidate with an application in progress."""
    candidate = Candidate.objects.create(
        id_number=VICTIM_NID, first_name="Victim", last_name="Person", email=VICTIM_EMAIL,
        phone="0770000000", address="1 Real Street", qualifications="BSc", experience="5 years",
        resume="recruitment/resumes/original.pdf",
    )
    JobApplication.objects.create(
        job=jobs["external"], candidate=candidate, cover_letter="Original letter", status="Interview"
    )
    return candidate


def snapshot(candidate):
    candidate.refresh_from_db()
    return {
        f: getattr(candidate, f)
        for f in ("id_number", "first_name", "last_name", "email", "phone", "address",
                  "date_of_birth", "qualifications", "experience")
    } | {"resume": candidate.resume.name}


# =============================================================================
# Jobs
# =============================================================================


@pytest.mark.django_db
class TestPublicJobs:
    def test_list_contains_only_open_jobs_internal_included(self, jobs):
        titles = {j["title"] for j in APIClient().get(f"{PUBLIC}/jobs/").json()}
        assert titles == {"External Open", "Internal Open"}

    @pytest.mark.parametrize("key", ["draft", "pending", "closed"])
    def test_non_open_detail_is_indistinguishable_from_missing(self, jobs, key):
        hidden = APIClient().get(f"{PUBLIC}/jobs/{jobs[key].id}/")
        missing = APIClient().get(f"{PUBLIC}/jobs/999999/")
        assert hidden.status_code == missing.status_code == 404
        assert hidden.json() == missing.json() == {"error": "Job not found"}

    def test_internal_open_detail_is_public(self, jobs):
        response = APIClient().get(f"{PUBLIC}/jobs/{jobs['internal'].id}/")
        assert response.status_code == 200
        assert response.json()["is_internal"] is True

    def test_list_and_detail_expose_exactly_the_allowlist(self, jobs, victim):
        listed = APIClient().get(f"{PUBLIC}/jobs/").json()
        detail = APIClient().get(f"{PUBLIC}/jobs/{jobs['external'].id}/").json()
        for job in [*listed, detail]:
            assert set(job) == PUBLIC_JOB_FIELDS
        assert "applicants_count" not in detail
        assert "notes" not in detail
        assert "INTERNAL HR NOTE" not in str(listed) + str(detail)

    def test_salary_is_public(self, jobs):
        detail = APIClient().get(f"{PUBLIC}/jobs/{jobs['external'].id}/").json()
        assert (detail["salary_usd_min"], detail["salary_usd_max"]) == ("1000.00", "2000.00")

    def test_internal_job_api_still_carries_applicant_count(self, jobs, victim, admin_client):
        detail = admin_client.get(f"/api/v2/recruitment/jobs/{jobs['external'].id}/").json()
        assert detail["applicants_count"] == 1


# =============================================================================
# check-application
# =============================================================================


@pytest.mark.django_db
class TestCheckApplication:
    def check(self, national_id, job):
        return APIClient().post(
            f"{PUBLIC}/jobs/check-application/", {"id_number": national_id, "job_id": job.id},
            format="json",
        )

    def test_returns_only_has_applied(self, jobs, victim):
        assert self.check(VICTIM_NID, jobs["external"]).json() == {"has_applied": True}
        assert self.check(VICTIM_NID, jobs["internal"]).json() == {"has_applied": False}
        assert self.check("00-000000Z00", jobs["external"]).json() == {"has_applied": False}

    def test_never_discloses_identity(self, jobs, victim):
        body = self.check(VICTIM_NID, jobs["internal"]).content.decode()
        assert "Victim" not in body
        assert "candidate" not in body


# =============================================================================
# Application integrity
# =============================================================================


@pytest.mark.django_db
class TestApplicationSubmission:
    def test_new_applicant_creates_candidate_and_application(self, jobs):
        response = apply(email="new@example.com", id_number="63-999999Z99",
                         first_name="New", job_id=jobs["external"].id)
        assert response.status_code == 201, response.content
        assert set(response.json()["application"]) == RECEIPT_FIELDS
        candidate = Candidate.objects.get(email="new@example.com")
        assert candidate.id_number == "63-999999Z99"
        assert JobApplication.objects.filter(candidate=candidate).count() == 1

    def test_receipt_carries_no_candidate_identity(self, jobs):
        body = apply(email="new@example.com", id_number="63-999999Z99",
                     job_id=jobs["external"].id).content.decode()
        assert "Victim" not in body and "new@example.com" not in body
        assert "candidate" not in body

    def test_same_applicant_same_job_updates_the_application(self, jobs, victim):
        before = snapshot(victim)
        response = apply(
            job_id=jobs["external"].id, cover_letter="Revised letter", phone="0771111111",
            address="2 New Street", qualifications="MSc", experience="6 years",
            resume=resume("updated.pdf"),
        )
        assert response.status_code == 200, response.content
        assert response.json()["message"] == "Application updated successfully"

        applications = JobApplication.objects.filter(candidate=victim, job=jobs["external"])
        assert applications.count() == 1
        application = applications.get()
        assert application.cover_letter == "Revised letter"
        assert (application.phone, application.address) == ("0771111111", "2 New Street")
        assert (application.qualifications, application.experience) == ("MSc", "6 years")
        assert application.resume.name.startswith("recruitment/resumes/")
        assert application.status == "Interview"  # only reviewers change status
        # The canonical candidate record is untouched by the resubmission.
        assert snapshot(victim) == before

    def test_same_applicant_email_match_is_case_insensitive(self, jobs, victim):
        response = apply(job_id=jobs["external"].id, email=VICTIM_EMAIL.upper())
        assert response.status_code == 200, response.content

    def test_resubmission_without_resume_keeps_the_one_on_file(self, jobs, victim):
        apply(job_id=jobs["internal"].id)
        stored = JobApplication.objects.get(candidate=victim, job=jobs["internal"]).resume.name
        # The public endpoint requires a resume; exercise the service path directly.
        from modules.recruitment.api.views import get_application_service
        from modules.recruitment.application.services import SubmitApplicationCommand

        result = get_application_service().submit_application(SubmitApplicationCommand(
            job_id=jobs["internal"].id, national_id=VICTIM_NID, email=VICTIM_EMAIL,
            cover_letter="No new resume",
        ))
        assert result.created is False
        application = JobApplication.objects.get(candidate=victim, job=jobs["internal"])
        assert application.resume.name == stored

    def test_same_applicant_new_job_creates_application_without_touching_candidate(self, jobs, victim):
        before = snapshot(victim)
        response = apply(job_id=jobs["internal"].id, phone="0772222222")
        assert response.status_code == 201, response.content
        assert JobApplication.objects.filter(candidate=victim).count() == 2
        assert JobApplication.objects.get(candidate=victim, job=jobs["internal"]).phone == "0772222222"
        assert snapshot(victim) == before

    def test_applicants_without_national_id_do_not_collide(self, jobs):
        first = apply(id_number="", email="a@example.com", job_id=jobs["external"].id)
        second = apply(id_number="", email="b@example.com", job_id=jobs["external"].id)
        assert (first.status_code, second.status_code) == (201, 201), second.content
        assert Candidate.objects.filter(id_number__isnull=True).count() == 2


@pytest.mark.django_db
class TestIdentityCollisions:
    """
    The REM-04 vulnerability: victim national ID + attacker contact/resume used
    to rewrite the victim's Candidate record and redirect their status emails.
    """

    def assert_refused(self, response, victim, before, applications_before):
        assert response.status_code == 400, response.content
        body = response.content.decode()
        assert "Victim" not in body and VICTIM_EMAIL not in body
        assert snapshot(victim) == before
        assert JobApplication.objects.count() == applications_before

    @pytest.mark.parametrize("job_key", ["external", "internal"], ids=["same-job", "other-job"])
    def test_victim_national_id_with_attacker_contact_is_refused(self, jobs, victim, job_key, tmp_path):
        before, count = snapshot(victim), JobApplication.objects.count()
        response = apply(
            job_id=jobs[job_key].id, email="attacker@example.com", first_name="Mallory",
            phone="0999999999", address="Elsewhere", cover_letter="Hijacked",
            resume=resume("attacker.pdf", b"%PDF-1.4 attacker"),
        )
        self.assert_refused(response, victim, before, count)
        assert JobApplication.objects.get(candidate=victim, job=jobs["external"]).cover_letter == "Original letter"
        # A refused submission stores no file.
        assert not list(tmp_path.rglob("*.pdf"))

    def test_victim_email_with_other_national_id_is_refused(self, jobs, victim):
        before, count = snapshot(victim), JobApplication.objects.count()
        response = apply(job_id=jobs["internal"].id, id_number="63-000000X00", phone="0999999999")
        self.assert_refused(response, victim, before, count)

    def test_victim_email_without_national_id_is_refused(self, jobs, victim):
        before, count = snapshot(victim), JobApplication.objects.count()
        response = apply(job_id=jobs["external"].id, id_number="", cover_letter="Hijacked")
        self.assert_refused(response, victim, before, count)

    def test_national_id_of_one_candidate_and_email_of_another_is_refused(self, jobs, victim):
        other = Candidate.objects.create(
            id_number="63-333333C33", first_name="Other", last_name="Person", email="other@example.com"
        )
        before_other = snapshot(other)
        before, count = snapshot(victim), JobApplication.objects.count()
        response = apply(job_id=jobs["internal"].id, email="other@example.com")
        self.assert_refused(response, victim, before, count)
        assert snapshot(other) == before_other

    def test_status_emails_still_reach_the_real_candidate(self, jobs, victim, admin_client, mailoutbox):
        apply(job_id=jobs["external"].id, email="attacker@example.com")
        application = JobApplication.objects.get(candidate=victim, job=jobs["external"])
        admin_client.post(f"/api/v2/recruitment/applications/{application.id}/status/",
                          {"status": "Offered"}, format="json")
        assert [m.to for m in mailoutbox] == [[VICTIM_EMAIL]]


@pytest.mark.django_db
class TestDecidedApplicationsAreImmutable:
    """
    Once HR has decided an application (Hired/Rejected), its submission is the
    evidence for that decision: an anonymous resubmission may not replace it.
    """

    def application(self, victim, jobs):
        return JobApplication.objects.get(candidate=victim, job=jobs["external"])

    def materials(self, application):
        application.refresh_from_db()
        return {
            f: getattr(application, f)
            for f in ("cover_letter", "phone", "address", "qualifications", "experience", "status")
        } | {"resume": application.resume.name, "candidate_id": application.candidate_id}

    @pytest.mark.parametrize("decision", ["Rejected", "Hired"])
    def test_resubmission_is_refused_and_nothing_changes(self, jobs, victim, decision, tmp_path):
        application = self.application(victim, jobs)
        application.status = decision
        application.phone, application.resume = "0770000000", "recruitment/resumes/original.pdf"
        application.save()
        before, before_candidate = self.materials(application), snapshot(victim)
        files_before = set(tmp_path.rglob("*"))

        response = apply(
            job_id=jobs["external"].id, cover_letter="Rewritten", phone="0999999999",
            address="Elsewhere", qualifications="Forged", experience="Forged",
            resume=resume("replacement.pdf"),
        )

        assert response.status_code == 400
        assert "already been decided" in response.json()["error"]
        assert self.materials(application) == before
        assert snapshot(victim) == before_candidate
        assert set(tmp_path.rglob("*")) == files_before  # no file stored

    @pytest.mark.parametrize("state", ["Pending", "Shortlisted", "Interview", "Offered"])
    def test_undecided_applications_still_accept_resubmission(self, jobs, victim, state):
        application = self.application(victim, jobs)
        application.status = state
        application.save()
        response = apply(job_id=jobs["external"].id, cover_letter="Revised")
        assert response.status_code == 200, response.content
        application.refresh_from_db()
        assert (application.cover_letter, application.status) == ("Revised", state)

    def test_portal_resubmission_of_a_decided_application_is_refused(self, jobs, victim):
        application = self.application(victim, jobs)
        application.status = "Rejected"
        application.save()
        response = APIClient().post(f"{PORTAL}/jobs/{jobs['external'].id}/apply/", {
            "national_id": VICTIM_NID, "first_name": "Victim", "last_name": "Person",
            "email": VICTIM_EMAIL, "phone": "0999999999", "date_of_birth": "1990-01-01",
            "cover_letter": "Rewritten via portal",
        }, format="json")
        assert response.status_code == 400
        application.refresh_from_db()
        assert application.cover_letter == "Original letter"

    def test_the_entity_enforces_it_too(self):
        from modules.recruitment.domain.entities import Application
        from modules.recruitment.domain.value_objects import ApplicationStatus
        from shared.domain.exceptions import ValidationError

        decided = Application(id=1, job_id=1, candidate_id=1, status=ApplicationStatus.REJECTED)
        with pytest.raises(ValidationError):
            decided.update_submission("x", "x", "x", "x", "x")


class TestNoIdCollisionOverwrite:
    """
    IDs used to be minted as max(id) + 1 and written with
    update_or_create(id=...): two concurrent submissions computing the same ID
    made the second one overwrite the first person's row. A new submission must
    never be able to update an existing Candidate, JobApplication or Job.
    """

    def test_no_repository_can_mint_ids(self):
        from modules.recruitment.application.interfaces import (
            IApplicationRepository, ICandidateRepository, IJobRepository,
        )
        from modules.recruitment.infrastructure.persistence.django_application_repository import (
            DjangoApplicationRepository,
        )
        from modules.recruitment.infrastructure.persistence.django_candidate_repository import (
            DjangoCandidateRepository,
        )
        from modules.recruitment.infrastructure.persistence.django_job_repository import DjangoJobRepository

        for cls in (IJobRepository, ICandidateRepository, IApplicationRepository,
                    DjangoJobRepository, DjangoCandidateRepository, DjangoApplicationRepository):
            assert not hasattr(cls, "get_next_id"), cls

    @pytest.mark.django_db
    def test_new_submission_rows_are_inserted_without_a_chosen_id(self, jobs, monkeypatch):
        from modules.recruitment.infrastructure.persistence import _save

        seen = []
        real = _save.insert_or_update

        def spy(model_class, entity_id, fields):
            seen.append((model_class.__name__, entity_id))
            return real(model_class, entity_id, fields)

        for module in ("django_candidate_repository", "django_application_repository"):
            monkeypatch.setattr(
                f"modules.recruitment.infrastructure.persistence.{module}.insert_or_update", spy
            )
        assert apply(job_id=jobs["external"].id, email="new@example.com",
                     id_number="63-999999Z99").status_code == 201
        assert seen == [("Candidate", None), ("JobApplication", None)]

    @pytest.mark.django_db
    def test_saving_an_unknown_id_is_refused_not_inserted(self, jobs):
        from modules.recruitment.domain.entities import Candidate as CandidateEntity
        from modules.recruitment.infrastructure.persistence.django_candidate_repository import (
            DjangoCandidateRepository,
        )
        from shared.domain.exceptions import NotFoundError

        ghost = CandidateEntity(id=424242, first_name="Ghost", last_name="Row", email="g@example.com")
        with pytest.raises(NotFoundError):
            DjangoCandidateRepository().save(ghost)
        assert not Candidate.objects.filter(pk=424242).exists()

    @pytest.mark.django_db
    def test_interleaved_new_records_get_distinct_rows(self, jobs, victim):
        """
        The old race, made deterministic: two new records are both prepared
        before either is written (where max(id) + 1 used to hand both the
        same ID). Each must become its own row, and the victim is untouched.
        """
        from modules.recruitment.domain.entities import Application, Candidate as CandidateEntity
        from modules.recruitment.infrastructure.persistence.django_application_repository import (
            DjangoApplicationRepository,
        )
        from modules.recruitment.infrastructure.persistence.django_candidate_repository import (
            DjangoCandidateRepository,
        )

        before = snapshot(victim)
        victim_application = JobApplication.objects.get(candidate=victim)
        candidates, applications = DjangoCandidateRepository(), DjangoApplicationRepository()

        first = CandidateEntity(id=None, first_name="First", last_name="Racer", email="first@example.com")
        second = CandidateEntity(id=None, first_name="Second", last_name="Racer", email="second@example.com")
        saved = [candidates.save(first), candidates.save(second)]
        assert len({victim.id, *(c.id for c in saved)}) == 3

        pending = [Application(id=None, job_id=jobs["internal"].id, candidate_id=c.id) for c in saved]
        saved_apps = [applications.save(a) for a in pending]
        assert len({victim_application.id, *(a.id for a in saved_apps)}) == 3

        assert snapshot(victim) == before
        victim_application.refresh_from_db()
        assert (victim_application.candidate_id, victim_application.job_id,
                victim_application.cover_letter) == (victim.id, jobs["external"].id, "Original letter")

    @pytest.mark.django_db
    def test_sequence_migration_moves_lagging_sequences_past_existing_rows(self, jobs):
        """
        Rows inserted with explicit IDs (the old max(id) + 1 scheme) leave a
        PostgreSQL sequence behind; migration 0003 must move it forward so a
        database-assigned insert does not collide with an existing row.
        """
        import importlib

        from django.db import connection

        if connection.vendor != "postgresql":
            pytest.skip("Sequences only lag on PostgreSQL")
        migration = importlib.import_module("modules.recruitment.migrations.0003_advance_id_sequences")

        # Reproduce a pre-REM-04 database: an explicit-ID row far ahead of the sequence.
        Candidate.objects.create(id=5000, first_name="Legacy", last_name="Row", email="legacy@example.com")

        class _Editor:
            pass

        editor = _Editor()
        editor.connection = connection
        migration.advance_sequences(None, editor)
        migration.advance_sequences(None, editor)  # idempotent

        fresh = Candidate.objects.create(first_name="New", last_name="Row", email="new@example.com")
        assert fresh.id > 5000
        assert Candidate.objects.get(pk=5000).first_name == "Legacy"

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_submissions_create_distinct_rows_and_leave_the_victim_intact(self, jobs, victim):
        import threading

        from django.db import connection

        if connection.vendor == "sqlite":
            pytest.skip(
                "SQLite's shared-cache in-memory test DB raises 'database table is "
                "locked' on concurrent writers instead of waiting; run on PostgreSQL"
            )

        from modules.recruitment.api.views import get_application_service
        from modules.recruitment.application.services import SubmitApplicationCommand

        victim_application = JobApplication.objects.get(candidate=victim)
        before = snapshot(victim)
        before_application = (victim_application.job_id, victim_application.cover_letter,
                              victim_application.status)
        count = 6
        barrier = threading.Barrier(count)
        errors = []

        def submit(i):
            try:
                barrier.wait()
                get_application_service().submit_application(SubmitApplicationCommand(
                    job_id=jobs["internal"].id, national_id=f"63-00000{i}C00",
                    first_name=f"Applicant{i}", last_name="Concurrent",
                    email=f"concurrent{i}@example.com", cover_letter=f"letter {i}",
                ))
            except Exception as exc:  # noqa: BLE001 - reported below
                errors.append(repr(exc))
            finally:
                connection.close()

        threads = [threading.Thread(target=submit, args=(i,)) for i in range(count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        created = Candidate.objects.filter(last_name="Concurrent")
        assert created.count() == count
        assert len({c.email for c in created}) == count
        assert JobApplication.objects.filter(candidate__in=created).count() == count
        assert snapshot(victim) == before
        victim_application.refresh_from_db()
        assert victim_application.candidate_id == victim.id
        assert (victim_application.job_id, victim_application.cover_letter,
                victim_application.status) == before_application


# =============================================================================
# Status lookup
# =============================================================================


@pytest.mark.django_db
class TestStatusLookup:
    def lookup(self, national_id):
        return APIClient().post(f"{PUBLIC}/applications/status/", {"id_number": national_id}, format="json")

    def test_known_id_returns_application_statuses(self, jobs, victim):
        response = self.lookup(VICTIM_NID)
        assert response.status_code == 200
        [row] = response.json()
        assert set(row) == STATUS_FIELDS
        assert (row["job_title"], row["status"]) == ("External Open", "Interview")

    def test_unknown_id_is_indistinguishable_from_no_applications(self, jobs):
        Candidate.objects.create(id_number="63-444444D44", first_name="No", last_name="Apps",
                                 email="noapps@example.com")
        unknown, no_apps = self.lookup("00-000000Z00"), self.lookup("63-444444D44")
        assert (unknown.status_code, unknown.json()) == (no_apps.status_code, no_apps.json()) == (200, [])

    def test_response_carries_no_candidate_identity(self, jobs, victim):
        body = self.lookup(VICTIM_NID).content.decode()
        assert "Victim" not in body and VICTIM_EMAIL not in body

    def test_view_goes_through_the_application_service(self, jobs, monkeypatch):
        from modules.recruitment.application.services import ApplicationService

        calls = []
        monkeypatch.setattr(
            ApplicationService, "lookup_application_status",
            lambda self, national_id: calls.append(national_id) or [],
        )
        self.lookup("63-555555E55")
        assert calls == ["63-555555E55"]

    def test_view_no_longer_touches_the_candidate_repository(self):
        from modules.recruitment.api import views

        assert "DjangoCandidateRepository" not in views.ApplicationStatusView.post.__code__.co_names


# =============================================================================
# Throttling
# =============================================================================


@pytest.mark.django_db
class TestThrottling:
    def test_every_anonymous_scope_has_a_configured_rate(self):
        from django.conf import settings

        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        for throttle in (throttles.RecruitmentApplyThrottle, throttles.RecruitmentCheckThrottle,
                         throttles.RecruitmentStatusThrottle):
            assert rates[throttle.scope]

    @pytest.fixture
    def tight(self, monkeypatch):
        rates = {"recruitment_apply": "2/min", "recruitment_check": "2/min", "recruitment_status": "2/min"}
        for throttle in (throttles.RecruitmentApplyThrottle, throttles.RecruitmentCheckThrottle,
                         throttles.RecruitmentStatusThrottle):
            monkeypatch.setattr(throttle, "THROTTLE_RATES", rates)

    def test_status_lookup_is_throttled(self, jobs, tight):
        codes = [APIClient().post(f"{PUBLIC}/applications/status/", {"id_number": f"63-{i}"},
                                  format="json").status_code for i in range(3)]
        assert codes == [200, 200, 429]

    def test_check_application_is_throttled(self, jobs, tight):
        codes = [APIClient().post(f"{PUBLIC}/jobs/check-application/",
                                  {"id_number": f"63-{i}", "job_id": jobs["external"].id},
                                  format="json").status_code for i in range(3)]
        assert codes == [200, 200, 429]

    def test_apply_is_throttled(self, jobs, tight):
        codes = [apply(job_id=jobs["external"].id, email=f"t{i}@example.com",
                       id_number=f"63-00000{i}T00").status_code for i in range(3)]
        assert codes == [201, 201, 429]

    def test_signing_in_does_not_lift_the_limit(self, jobs, tight):
        user = get_user_model().objects.create_user(email="signed@zchpc.test", password="Pass12345!")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
        codes = [client.post(f"{PUBLIC}/applications/status/", {"id_number": "63-1"},
                             format="json").status_code for _ in range(3)]
        assert codes[-1] == 429

    def test_portal_routes_share_the_budget(self, jobs, tight):
        client = APIClient()
        client.post(f"{PUBLIC}/applications/status/", {"id_number": "63-1"}, format="json")
        client.post(f"{PORTAL}/applications/status/", {"national_id": "63-1"}, format="json")
        assert client.post(f"{PORTAL}/applications/status/", {"national_id": "63-1"},
                           format="json").status_code == 429


@pytest.mark.django_db
class TestThrottleClientIdentity:
    """
    X-Forwarded-For is only trustworthy for entries a trusted proxy appended.
    With NUM_PROXIES left as None, DRF keyed throttles on the whole
    client-supplied header, so rotating it gave every request a fresh budget.
    """

    STATUS = f"{PUBLIC}/applications/status/"

    @pytest.fixture(autouse=True)
    def tight(self, monkeypatch):
        monkeypatch.setattr(throttles.RecruitmentStatusThrottle, "THROTTLE_RATES",
                            {"recruitment_status": "2/min"})

    @pytest.fixture
    def behind_one_proxy(self, settings):
        settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}

    def lookup(self, client, **meta):
        return client.post(self.STATUS, {"id_number": "63-1"}, format="json", **meta).status_code

    def test_default_trusts_no_proxy(self):
        from django.conf import settings

        assert settings.REST_FRAMEWORK["NUM_PROXIES"] == 0

    def test_rotating_forwarded_for_does_not_reset_the_limit(self, jobs):
        client = APIClient()
        codes = [self.lookup(client, REMOTE_ADDR="198.51.100.7", HTTP_X_FORWARDED_FOR=f"10.0.0.{i}")
                 for i in range(5)]
        assert codes == [200, 200, 429, 429, 429]

    def test_distinct_clients_have_independent_budgets(self, jobs):
        client = APIClient()
        first = [self.lookup(client, REMOTE_ADDR="198.51.100.7") for _ in range(3)]
        second = [self.lookup(client, REMOTE_ADDR="198.51.100.8") for _ in range(2)]
        assert (first, second) == ([200, 200, 429], [200, 200])

    def test_behind_nginx_forged_leading_entries_are_ignored(self, jobs, behind_one_proxy):
        # nginx appends the real peer; whatever the client prepended varies.
        client = APIClient()
        codes = [self.lookup(client, REMOTE_ADDR="172.18.0.5",
                             HTTP_X_FORWARDED_FOR=f"10.0.0.{i}, 203.0.113.9") for i in range(4)]
        assert codes == [200, 200, 429, 429]

    def test_behind_nginx_distinct_clients_have_independent_budgets(self, jobs, behind_one_proxy):
        client = APIClient()
        first = [self.lookup(client, REMOTE_ADDR="172.18.0.5", HTTP_X_FORWARDED_FOR="203.0.113.9")
                 for _ in range(3)]
        second = [self.lookup(client, REMOTE_ADDR="172.18.0.5", HTTP_X_FORWARDED_FOR="203.0.113.10")
                  for _ in range(2)]
        assert (first, second) == ([200, 200, 429], [200, 200])


# =============================================================================
# Resumes
# =============================================================================


@pytest.mark.django_db
class TestResumeBoundary:
    def test_resume_is_stored_under_an_unguessable_name(self, jobs):
        apply(job_id=jobs["external"].id, email="cv@example.com", id_number="63-777777G77",
              resume=resume("Jane Doe CV.pdf"))
        application = JobApplication.objects.get(candidate__email="cv@example.com")
        assert re.fullmatch(r"recruitment/resumes/[0-9a-f]{32}\.pdf", application.resume.name)
        assert "Jane" not in application.resume.name

    def test_no_public_response_mentions_a_resume(self, jobs, victim):
        client = APIClient()
        bodies = [
            client.get(f"{PUBLIC}/jobs/").content,
            client.get(f"{PUBLIC}/jobs/{jobs['external'].id}/").content,
            apply(job_id=jobs["external"].id).content,
            client.post(f"{PUBLIC}/applications/status/", {"id_number": VICTIM_NID}, format="json").content,
            client.post(f"{PUBLIC}/jobs/check-application/",
                        {"id_number": VICTIM_NID, "job_id": jobs["external"].id}, format="json").content,
        ]
        for body in bodies:
            text = body.decode()
            assert "resume" not in text.lower() and "/media" not in text


# =============================================================================
# Portal careers routes
# =============================================================================


@pytest.mark.django_db
class TestPortalCareersRoutes:
    def portal_apply(self, job, **overrides):
        payload = {
            "national_id": VICTIM_NID, "first_name": "Victim", "last_name": "Person",
            "email": VICTIM_EMAIL, "phone": "0770000000", "date_of_birth": "1990-01-01",
            "cover_letter": "Via portal",
        }
        payload.update(overrides)
        return APIClient().post(f"{PORTAL}/jobs/{job.id}/apply/", payload, format="json")

    def test_job_list_and_detail_follow_the_public_rules(self, jobs):
        titles = {j["title"] for j in APIClient().get(f"{PORTAL}/jobs/").json()}
        assert titles == {"External Open", "Internal Open"}
        assert APIClient().get(f"{PORTAL}/jobs/{jobs['draft'].id}/").status_code == 404
        detail = APIClient().get(f"{PORTAL}/jobs/{jobs['external'].id}/").json()
        assert "applicants_count" not in detail

    def test_apply_works_through_the_recruitment_service(self, jobs):
        response = self.portal_apply(jobs["external"], national_id="63-888888H88",
                                     email="portal@example.com")
        assert response.status_code == 201, response.content
        assert Candidate.objects.get(email="portal@example.com").id_number == "63-888888H88"

    def test_apply_collision_is_refused(self, jobs, victim):
        before = snapshot(victim)
        response = self.portal_apply(jobs["internal"], email="attacker@example.com",
                                     first_name="Mallory")
        assert response.status_code == 400
        assert "Victim" not in response.content.decode()
        assert snapshot(victim) == before

    def test_status_lookup_works(self, jobs, victim):
        response = APIClient().post(f"{PORTAL}/applications/status/", {"national_id": VICTIM_NID},
                                    format="json")
        assert response.status_code == 200, response.content
        assert [row["job_title"] for row in response.json()] == ["External Open"]
        unknown = APIClient().post(f"{PORTAL}/applications/status/", {"national_id": "00-0"},
                                   format="json")
        assert (unknown.status_code, unknown.json()) == (200, [])

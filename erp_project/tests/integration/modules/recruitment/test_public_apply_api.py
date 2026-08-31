"""
Regression test for POST /api/v2/recruitment/public/jobs/apply/.

SubmitApplicationRequestSerializer used to expose its ID-number field as
"national_id", while its siblings (CheckApplicationRequestSerializer,
ApplicationStatusCheckRequestSerializer) and the actual frontend
(employee-portal/src/services/jobs.service.ts) all use "id_number". Since
the field was required=False, this didn't error - it silently dropped the
applicant's ID number into the DB as blank.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.integration

APPLY_URL = "/api/v2/recruitment/public/jobs/apply/"


@pytest.fixture
def open_public_job(db):
    from modules.hr.infrastructure.persistence.models import Department
    from modules.recruitment.infrastructure.persistence.models import Job

    department = Department.objects.create(name="Systems Support", description="")
    return Job.objects.create(
        title="Public Test Role",
        status="Open",
        is_internal=False,
        location="Harare",
        department=department,
    )


@pytest.mark.django_db
class TestPublicApplyAPI:
    def test_submitted_id_number_is_saved_on_the_candidate(self, open_public_job):
        resume = SimpleUploadedFile(
            "resume.pdf", b"%PDF-1.4 fake resume content", content_type="application/pdf"
        )
        payload = {
            "job_id": open_public_job.id,
            "id_number": "63-123456A78",
            "first_name": "Jane",
            "last_name": "Applicant",
            "email": "jane.applicant@example.com",
            "phone": "0771234567",
            "address": "Harare",
            "qualifications": "BSc Computer Science",
            "experience": "2 years",
            "cover_letter": "I'd like to apply.",
            "resume": resume,
        }

        response = APIClient().post(APPLY_URL, payload, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED, response.content

        from modules.recruitment.infrastructure.persistence.models import Candidate

        candidate = Candidate.objects.get(email="jane.applicant@example.com")
        assert candidate.id_number == "63-123456A78"

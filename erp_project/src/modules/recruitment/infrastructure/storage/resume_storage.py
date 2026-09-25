"""
Resume storage for job applications.

Resumes live under MEDIA_ROOT, which nginx serves directly at /media/ without
any Django authorization (a cross-module issue tracked separately from
REM-04). Until that is addressed, a stored resume must not be reachable by
guessing its URL: the applicant's own filename (often "resume.pdf" or
"<Full Name> CV.pdf") is discarded and replaced with 128 random bits.
"""

import os
import uuid

from django.core.files.storage import default_storage

RESUME_DIRECTORY = "recruitment/resumes"


class DjangoResumeStorage:
    """IResumeStorage backed by Django's default storage, with unguessable names."""

    def save(self, uploaded_file) -> str:
        extension = os.path.splitext(uploaded_file.name or "")[1].lower()
        name = f"{RESUME_DIRECTORY}/{uuid.uuid4().hex}{extension}"
        return default_storage.save(name, uploaded_file)

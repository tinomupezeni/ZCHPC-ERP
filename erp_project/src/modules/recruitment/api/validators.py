"""
Resume file validation for job applications.
"""
from rest_framework.exceptions import ValidationError

ALLOWED_RESUME_EXTENSIONS = (".pdf", ".doc", ".docx")
MAX_RESUME_SIZE_MB = 10


def validate_resume_file(uploaded_file) -> None:
    """
    Server-side validation for a resume upload.

    Raises rest_framework.exceptions.ValidationError if the file is
    missing, empty, too large, has a disallowed extension, or its
    actual content doesn't match its claimed file type.
    """
    if uploaded_file is None:
        raise ValidationError({"resume": "A resume file is required."})

    name = uploaded_file.name.lower()
    if not name.endswith(ALLOWED_RESUME_EXTENSIONS):
        raise ValidationError(
            {"resume": "Resume must be a PDF or Word document (.pdf, .doc, .docx)."}
        )

    if uploaded_file.size == 0:
        raise ValidationError({"resume": "The uploaded resume is empty."})

    max_bytes = MAX_RESUME_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(
            {"resume": f"Resume must be smaller than {MAX_RESUME_SIZE_MB}MB."}
        )

    # Check the file's actual content, not just its extension/name — this
    # catches a renamed .exe/.zip masquerading as a .pdf/.docx.
    header = uploaded_file.read(8)
    uploaded_file.seek(0)  # reset the pointer so the file can still be saved fully

    is_pdf = header.startswith(b"%PDF")
    is_docx = header.startswith(b"PK\x03\x04")  # .docx is a zip archive
    is_legacy_doc = header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")  # OLE format

    if name.endswith(".pdf") and not is_pdf:
        raise ValidationError({"resume": "This file isn't a valid PDF."})
    if name.endswith(".docx") and not is_docx:
        raise ValidationError({"resume": "This file isn't a valid Word (.docx) document."})
    if name.endswith(".doc") and not is_legacy_doc:
        raise ValidationError({"resume": "This file isn't a valid Word (.doc) document."})
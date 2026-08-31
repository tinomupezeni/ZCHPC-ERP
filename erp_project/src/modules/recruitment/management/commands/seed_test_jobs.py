"""
Management command to seed realistic job postings for functionality testing.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

JOBS = [
    {
        # Clearly labeled as a test fixture (not a real posting) - the two
        # HPC Platforms roles below are real internal-only postings and
        # correctly don't appear on the public careers page; this one exists
        # so the public listing/apply flow has something to test against.
        "title": "[TEST] QA Careers Page Verification Role",
        "department_name": "Systems Support",
        "reports_to": "Director - Systems Support",
        "location": "Harare, Zimbabwe",
        "is_internal": False,
        "status": "Open",
        "description": (
            "Test fixture used to verify the public careers page and application "
            "flow end-to-end. Not a real opening - safe to close/delete once "
            "testing is done."
        ),
        "responsibilities": [
            "Exist as a public, open, non-internal job for QA purposes.",
        ],
        "qualifications": [
            "N/A - test fixture.",
        ],
        "competencies": [
            "N/A - test fixture.",
        ],
        "application_process": (
            "This is a test posting for verifying the public application flow. "
            "Applications submitted here are test data."
        ),
        "contact_email": "hr@hpc.ac.zw",
        "notes": "Test fixture - not a real job opening.",
    },
    {
        "title": "Systems Engineer - HPC Platforms",
        "department_name": "Systems Support",
        "reports_to": "Director - Systems Support",
        "location": "Harare, Zimbabwe",
        "is_internal": True,
        "status": "Open",
        "description": "Internal Career Opportunity",
        "responsibilities": [
            "Plan and implement installation, configuration, monitoring, and basic troubleshooting of HPC, cloud, and data centre platforms, including servers, operating systems, virtualisation, containerisation and storage systems.",
            "Design and implement procedures for monitoring system health, performance, logs, and alerts across HPC clusters, cloud platforms, and critical services, and escalate faults in accordance with incident management procedures.",
            "Plan and implement operational tasks such as system startups and shutdowns, user account setup, access management, backups, and scheduled maintenance activities.",
            "Manage deployment of software updates, patches, and configuration changes under approved change management processes.",
            "Supervise data centre operations, including network configurations, rack-and-stack activities, cabling, hardware replacement, and coordination with facilities and infrastructure teams.",
            "Design and supervise accurate operational records, system logs, asset information, and daily inspection checklists, and update job cards or tickets as required.",
            "Comply with information security, safety, and operational procedures, and support audits, inspections, and business continuity activities related to HPC and cloud services.",
        ],
        "qualifications": [
            "A university degree in High Performance Computing, Cloud Engineering, Computer Engineering, Computer Science, Computer Network Engineering, Cyber Security or a closely related field. Or completing within the quarter.",
            "Minimum of 1 year of demonstrable and confirmable experience in developing and configuring HPC and cloud platforms.",
            "Recognised professional certification in a relevant field is an added advantage.",
        ],
        "competencies": [
            "Meticulous attention to detail and analytical thinking.",
            "Strong organisational and time management skills.",
            "Teamwork and innovativeness.",
            "High ethical standards and confidentiality.",
            "Ability to work overtime and to handle pressure.",
        ],
        "application_process": (
            "Submit an application letter, copies of certificates, and a CV with full personal "
            "details (including full names, date of birth, qualifications, experience, and three "
            "referees). Applications should be sent to the address below by 20 May 2026, clearly "
            "indicating the position applied for.\n\n"
            "Address:\nThe Director\nZimbabwe Centre for High Performance Computing\n"
            "Zimbabwe Science Park 1\n630 Churchill Avenue,\nMount Pleasant,\nHARARE, Zimbabwe"
        ),
        "contact_email": "hr@hpc.ac.zw",
        "notes": (
            "Advert is open only to internal candidates; that is ZCHPC staff, Resident "
            "Innovators, Interns and Volunteer Experts.\n"
            "Only shortlisted candidates will be invited for interviews.\n"
            "Female candidates are encouraged to apply."
        ),
    },
    {
        "title": "Systems Technician - HPC Platforms",
        "department_name": "Systems Support",
        "reports_to": "Director - Systems Support",
        "location": "Harare, Zimbabwe",
        "is_internal": True,
        "status": "Open",
        "description": "Internal Career Opportunity Re-advertisement",
        "responsibilities": [
            "Perform routine installation, configuration, monitoring, and basic troubleshooting of HPC, cloud, and data centre platforms, including servers, operating systems, virtualisation, containerisation and storage systems.",
            "Monitor system health, performance, logs, and alerts across HPC clusters, cloud platforms, and critical services, and escalate faults in accordance with incident management procedures.",
            "Execute approved operational tasks such as system startups and shutdowns, user account setup, access management, backups, and scheduled maintenance activities.",
            "Assist with deployment of software updates, patches, and configuration changes under approved change management processes.",
            "Support data centre ICT operations, including network configuration, rack-and-stack activities, cabling, hardware replacement, and coordination with facilities and infrastructure teams.",
            "Maintain accurate operational records, system logs, asset information, and daily inspection checklists, and update job cards or tickets as required.",
            "Comply with information security, safety, and operational procedures, and support audits, inspections, and business continuity activities related to HPC and cloud services.",
        ],
        "qualifications": [
            "A university degree or recognised diploma in High Performance Computing, Computer Engineering, Network Engineering, Electronic Engineering, ICT or a closely related field. Or completing within the quarter.",
            "Recognised relevant certifications will be an added advantage.",
            "At least 1 year demonstrable and confirmable practical experience in developing, and configuring HPC and cloud platforms and infrastructure.",
        ],
        "competencies": [
            "Meticulous attention to detail and analytical thinking.",
            "Strong organisational and time management skills.",
            "Teamwork and innovativeness.",
            "High ethical standards and confidentiality.",
            "Ability to work overtime and to handle pressure.",
        ],
        "application_process": (
            "Submit an application letter, copies of certificates, and a CV with full personal "
            "details (including full names, date of birth, qualifications, experience, and three "
            "referees). Applications should be sent to the email address below by 20 May 2026, "
            "clearly indicating the position applied for.\n\n"
            "Address:\nThe Director\nZimbabwe Centre for High Performance Computing\n"
            "Zimbabwe Science Park 1\n630 Churchill Avenue,\nMount Pleasant,\nHARARE, Zimbabwe"
        ),
        "contact_email": "hr@hpc.ac.zw",
        "notes": (
            "Advert is open only to internal candidates; that is ZCHPC staff, Resident "
            "Innovators, Interns and Volunteer Experts.\n"
            "Only shortlisted candidates will be invited for interviews.\n"
            "Female candidates are encouraged to apply."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed realistic recruitment job postings for functionality testing."

    def handle(self, *args, **options):
        from modules.hr.infrastructure.persistence.models import Department, Position
        from modules.recruitment.infrastructure.persistence.models import Job

        with transaction.atomic():
            for job_data in JOBS:
                department, dept_created = Department.objects.get_or_create(
                    name=job_data["department_name"]
                )
                if dept_created:
                    self.stdout.write(self.style.SUCCESS(f"Created department: {department.name}"))

                position, pos_created = Position.objects.get_or_create(
                    title=job_data["title"],
                    defaults={"department": department},
                )
                if pos_created:
                    self.stdout.write(self.style.SUCCESS(f"Created position: {position.title}"))

                job, job_created = Job.objects.get_or_create(
                    title=job_data["title"],
                    defaults={
                        "department": department,
                        "position": position,
                        "status": job_data["status"],
                        "location": job_data["location"],
                        "reports_to": job_data["reports_to"],
                        "is_internal": job_data["is_internal"],
                        "description": job_data["description"],
                        "responsibilities": job_data["responsibilities"],
                        "qualifications": job_data["qualifications"],
                        "competencies": job_data["competencies"],
                        "application_process": job_data["application_process"],
                        "contact_email": job_data["contact_email"],
                        "notes": job_data["notes"],
                    },
                )
                if job_created:
                    self.stdout.write(self.style.SUCCESS(f"Created job posting: {job.title}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Job posting already exists: {job.title}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone - {len(JOBS)} job posting(s) seeded (idempotent, safe to re-run)."))

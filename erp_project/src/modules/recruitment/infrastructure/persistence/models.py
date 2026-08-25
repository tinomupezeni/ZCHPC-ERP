"""
Django models for the Recruitment module.
"""
from django.db import models
from django.utils import timezone


class Job(models.Model):
    """Job posting for recruitment."""
    STATUS_CHOICES = [
        ('Open', 'Open'), ('Closed', 'Closed'),
        ('Draft', 'Draft'), ('Pending', 'Pending')
    ]

    title = models.CharField(max_length=200)
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    position = models.ForeignKey(
        'hr.Position',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='job_postings'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    location = models.CharField(max_length=100, default="Harare")
    salary_usd_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_usd_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_zig_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_zig_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reports_to = models.CharField(max_length=200, default="ZCHPC Director")
    is_internal = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    qualifications = models.JSONField(default=list, blank=True)
    competencies = models.JSONField(default=list, blank=True)
    application_process = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(default="hroffice@zchpc.ac.zw")
    notes = models.TextField(blank=True, null=True)
    posted_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'human_resources_job'
        ordering = ['-created_at']

    @property
    def applicants_count(self):
        return self.applications.count()

    def save(self, *args, **kwargs):
        if self.position and not self.department:
            self.department = self.position.department
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.status})"


class Candidate(models.Model):
    """Job candidate."""
    id_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    qualifications = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'human_resources_candidate'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class JobApplication(models.Model):
    """Job application linking candidate to job."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'), ('Shortlisted', 'Shortlisted'),
        ('Interview', 'Interview'), ('Offered', 'Offered'),
        ('Hired', 'Hired'), ('Rejected', 'Rejected')
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        db_table = 'human_resources_jobapplication'
        unique_together = ('job', 'candidate')
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.candidate} for {self.job.title}"

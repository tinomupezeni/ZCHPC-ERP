from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import secrets
import string


class ExpenseCategory(models.Model):
    """
    Categories for expense claims.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum claimable amount for this category"
    )
    requires_receipt = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseClaim(models.Model):
    """
    Employee expense claims for reimbursement.
    """
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Paid', 'Paid'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('ZiG', 'Zimbabwe Gold'),
    ]

    employee = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.CASCADE,
        related_name='expense_claims'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='claims'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    date_incurred = models.DateField()
    receipt = models.FileField(
        upload_to='expense_receipts/%Y/%m/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft'
    )

    # Submission tracking
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Review tracking
    reviewed_by = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_expenses'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Payment tracking
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Expense Claim"
        verbose_name_plural = "Expense Claims"

    def __str__(self):
        return f"{self.title} - {self.employee.employee_id} - {self.amount} {self.currency}"

    @property
    def can_edit(self):
        """Check if the claim can be edited"""
        return self.status == 'Draft'

    @property
    def can_submit(self):
        """Check if the claim can be submitted"""
        return self.status == 'Draft'

    @property
    def can_cancel(self):
        """Check if the claim can be cancelled"""
        return self.status in ['Draft', 'Submitted']


class SupportTicket(models.Model):
    """
    Support tickets for IT, HR, or other departments.
    """
    CATEGORY_CHOICES = [
        ('IT', 'IT Support'),
        ('HR', 'Human Resources'),
        ('Facilities', 'Facilities'),
        ('Finance', 'Finance'),
        ('Other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Waiting', 'Waiting for Response'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    employee = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')

    # Assignment
    assigned_to = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: TKT-YYYYMMDD-XXXX
            from django.utils import timezone
            import random
            date_str = timezone.now().strftime('%Y%m%d')
            random_suffix = random.randint(1000, 9999)
            self.ticket_number = f"TKT-{date_str}-{random_suffix}"
        super().save(*args, **kwargs)

    @property
    def can_close(self):
        """Check if ticket can be closed by employee"""
        return self.status in ['Open', 'Resolved', 'Waiting']

    @property
    def can_reopen(self):
        """Check if ticket can be reopened"""
        return self.status == 'Closed'


class TicketMessage(models.Model):
    """
    Messages/replies in a support ticket thread.
    """
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.CASCADE,
        related_name='ticket_messages'
    )
    message = models.TextField()
    attachment = models.FileField(
        upload_to='ticket_attachments/%Y/%m/',
        null=True,
        blank=True
    )
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal notes not visible to ticket creator"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Ticket Message"
        verbose_name_plural = "Ticket Messages"

    def __str__(self):
        return f"Message on {self.ticket.ticket_number} by {self.sender.employee_id}"


class Notification(models.Model):
    """
    Notifications for employees in the employee portal.
    """
    NOTIFICATION_TYPES = [
        ('leave_approved', 'Leave Approved'),
        ('leave_rejected', 'Leave Rejected'),
        ('leave_request', 'New Leave Request'),
        ('expense_approved', 'Expense Approved'),
        ('expense_rejected', 'Expense Rejected'),
        ('ticket_update', 'Ticket Update'),
        ('ticket_resolved', 'Ticket Resolved'),
        ('payslip_available', 'Payslip Available'),
        ('announcement', 'Announcement'),
        ('system', 'System Notification'),
    ]

    employee = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.CASCADE,
        related_name='portal_notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Optional link to related object
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.employee.employee_id}"

    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class DocumentCategory(models.Model):
    """
    Categories for organizing company documents.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name for display"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """
    Company documents available to employees in the portal.
    """
    VISIBILITY_CHOICES = [
        ('all', 'All Employees'),
        ('department', 'Department Only'),
        ('specific', 'Specific Employees'),
    ]

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='documents'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='portal_documents/%Y/%m/')
    file_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Auto-detected file type (pdf, doc, xls, etc.)"
    )
    file_size = models.PositiveIntegerField(
        default=0,
        help_text="File size in bytes"
    )

    # Access control
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='all'
    )
    departments = models.ManyToManyField(
        'human_resources.Department',
        blank=True,
        related_name='accessible_documents',
        help_text="Departments that can access this document (when visibility is 'department')"
    )
    allowed_employees = models.ManyToManyField(
        'human_resources.Employees',
        blank=True,
        related_name='specific_documents',
        help_text="Specific employees who can access this document (when visibility is 'specific')"
    )

    # Version control
    version = models.CharField(max_length=20, default='1.0')
    is_latest = models.BooleanField(default=True)
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )

    # Metadata
    uploaded_by = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    is_active = models.BooleanField(default=True)
    requires_acknowledgement = models.BooleanField(
        default=False,
        help_text="Employees must acknowledge reading this document"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Statistics
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        # Auto-detect file type from extension
        if self.file:
            import os
            ext = os.path.splitext(self.file.name)[1].lower().lstrip('.')
            self.file_type = ext
            # Get file size
            try:
                self.file_size = self.file.size
            except (AttributeError, ValueError):
                pass
        super().save(*args, **kwargs)

    def can_access(self, employee):
        """Check if an employee can access this document"""
        if not self.is_active:
            return False
        if self.visibility == 'all':
            return True
        if self.visibility == 'department':
            return self.departments.filter(id=employee.department_id).exists()
        if self.visibility == 'specific':
            return self.allowed_employees.filter(id=employee.id).exists()
        return False


class DocumentAcknowledgement(models.Model):
    """
    Tracks which employees have acknowledged reading a document.
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='acknowledgements'
    )
    employee = models.ForeignKey(
        'human_resources.Employees',
        on_delete=models.CASCADE,
        related_name='document_acknowledgements'
    )
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ['document', 'employee']
        ordering = ['-acknowledged_at']
        verbose_name = "Document Acknowledgement"
        verbose_name_plural = "Document Acknowledgements"

    def __str__(self):
        return f"{self.employee.employee_id} acknowledged {self.document.title}"


class AttendanceQRToken(models.Model):
    """
    Dynamic QR tokens for attendance clock-in.
    Tokens rotate every 30 seconds to prevent fraud.
    """
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Track which tokens have been used (for audit trail)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Attendance QR Token"
        verbose_name_plural = "Attendance QR Tokens"

    def __str__(self):
        return f"QR Token {self.token[:8]}... (expires: {self.expires_at})"

    @classmethod
    def generate_token(cls):
        """Generate a cryptographically secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))

    @classmethod
    def get_or_create_current_token(cls, validity_seconds=30):
        """
        Get the current valid token or create a new one.
        Tokens are valid for `validity_seconds` (default 30 seconds).
        """
        from django.utils import timezone

        now = timezone.now()

        # Try to get an active, non-expired token
        current_token = cls.objects.filter(
            is_active=True,
            expires_at__gt=now
        ).order_by('-created_at').first()

        if current_token:
            return current_token

        # Deactivate all old tokens
        cls.objects.filter(is_active=True).update(is_active=False)

        # Create a new token
        from datetime import timedelta
        new_token = cls.objects.create(
            token=cls.generate_token(),
            expires_at=now + timedelta(seconds=validity_seconds)
        )

        return new_token

    @classmethod
    def verify_token(cls, token_string):
        """
        Verify if a token is valid.
        Returns the token object if valid, None otherwise.
        """
        from django.utils import timezone

        try:
            token = cls.objects.get(
                token=token_string,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return token
        except cls.DoesNotExist:
            return None

    def increment_usage(self):
        """Increment the usage counter for this token."""
        self.used_count += 1
        self.save(update_fields=['used_count'])

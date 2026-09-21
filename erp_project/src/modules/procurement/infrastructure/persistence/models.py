"""
Django models for the Procurement module.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Vendor(models.Model):
    """Supplier/Vendor for procurement."""
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_vendor'

    def __str__(self):
        return self.name


class BudgetCenter(models.Model):
    """Budget center for tracking procurement spend."""
    name = models.CharField(max_length=255)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    used_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'procurement_budgetcenter'

    @property
    def remaining_amount(self):
        return self.allocated_amount - self.used_amount

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Inventory item for procurement."""
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.IntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'procurement_inventoryitem'

    def __str__(self):
        return self.name


class PurchaseRequest(models.Model):
    """
    Purchase request matching the organisation's paper PR form.

    Workflow: DRAFT -> PENDING_DEPARTMENT_HEAD -> PENDING_ACCOUNTS
              -> PENDING_GM -> PENDING_DIRECTOR -> PENDING_PROCUREMENT
              -> PROCESSED
    Any stage may reject; rejected requests can be corrected and resubmitted.
    """

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_DEPARTMENT_HEAD', 'Pending Department Head'),
        ('PENDING_ACCOUNTS', 'Pending Accounts'),
        ('PENDING_GM', 'Pending General Manager'),
        ('PENDING_DIRECTOR', 'Pending Director'),
        ('PENDING_PROCUREMENT', 'Pending Procurement'),
        ('PROCESSED', 'Processed'),
        ('REJECTED', 'Rejected'),
    ]

    requisition_number = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='Auto-generated in format PR-00001',
    )

    # Section A — Requester information
    requester = models.ForeignKey(
        'hr.Employees', on_delete=models.PROTECT,
        related_name='purchase_requests',
    )
    department = models.ForeignKey(
        'hr.Department', on_delete=models.PROTECT,
    )
    designation = models.CharField(
        max_length=100,
        help_text='Request-time snapshot of position/designation',
    )
    contact = models.CharField(
        max_length=100,
        help_text='Request-time snapshot of contact details',
    )

    # Workflow
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='DRAFT',
    )

    # Section B — Totals
    total_estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Sum of line-item estimated costs',
    )

    # Section D — Procurement processing
    processed_by = models.ForeignKey(
        'hr.Employees', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='processed_purchase_requests',
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    purchase_order_number = models.CharField(
        max_length=50, null=True, blank=True, unique=True,
        help_text='Manually entered by Procurement at processing time (F23) - not auto-generated',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchaserequest'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='pr_status_idx'),
            models.Index(fields=['requisition_number'], name='pr_req_number_idx'),
            models.Index(fields=['-created_at'], name='pr_created_at_idx'),
            models.Index(fields=['requester'], name='pr_requester_idx'),
            models.Index(fields=['department'], name='pr_department_idx'),
            models.Index(fields=['purchase_order_number'], name='pr_po_number_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_estimated_cost__gte=0),
                name='pr_total_estimated_cost_non_negative',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            super().save(*args, **kwargs)
            self.requisition_number = f'PR-{self.pk:05d}'
            return super().save(update_fields=['requisition_number'])
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.requisition_number or 'PR (unsaved)'


class PurchaseRequestItem(models.Model):
    """
    Line item on a purchase request (Section B of the paper form).

    estimated_cost is a PER-UNIT price. The request's total_estimated_cost
    is the sum, across items, of quantity x estimated_cost.
    """

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
    )
    description = models.TextField(
        help_text='Description of the item or service required',
    )
    quantity = models.PositiveIntegerField()
    expected_delivery_period = models.CharField(
        max_length=100,
        help_text='Expected delivery timeframe, e.g. "2 weeks"',
    )
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Total estimated cost for this line (not unit cost)',
    )
    category = models.ForeignKey(
        'procurement.PurchaseRequestCategory', on_delete=models.PROTECT,
        related_name='items',
        help_text='Employee-facing category chosen by the requester (descriptive only)',
    )
    budget_code = models.ForeignKey(
        'accounts.AccountChart', on_delete=models.PROTECT,
        null=True, blank=True,
        help_text='Authoritative Chart of Accounts entry; assigned by Accounts, NULL until then',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_purchaserequestitem'
        indexes = [
            models.Index(fields=['purchase_request'], name='pri_purchase_request_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name='pri_quantity_gte_1',
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_cost__gte=0),
                name='pri_estimated_cost_non_negative',
            ),
        ]

    def __str__(self):
        return f"{self.description[:50]} x {self.quantity}"


class PurchaseRequestCategory(models.Model):
    """
    Employee-facing Purchase Request category (Slice F11-A).

    This is the mapping foundation described in the F11 investigation:
    PurchaseRequestCategory -> AccountChart. It exists so an employee can
    pick a plain-language category ("IT Consumables") instead of a raw GL
    code - AccountChart remains the sole source of truth for the account
    itself (code, name, external_account_type); nothing here duplicates
    those fields, only references the row via account_chart_id.

    The mapping is Finance-curated, not inferred: there is deliberately no
    keyword matching, code-prefix logic, or description-based guessing
    anywhere in how a category resolves to an account (see
    modules.procurement.application.use_cases.purchase_request_use_cases
    .CreatePurchaseRequest._resolve_budget_code_id). A category with no
    obvious, unambiguous account is simply not seeded, rather than mapped
    to a guess - see the F11 investigation's Bucket B/C/D categories and
    the funding-source-ambiguous ones, none of which are seeded here.

    account_chart is a OneToOneField rather than a plain ForeignKey so two
    employee-facing categories can never silently point at the same GL
    account.
    """

    name = models.CharField(
        max_length=100, unique=True,
        help_text='Employee-facing label, e.g. "IT Consumables" - not a GL account name',
    )
    account_chart = models.OneToOneField(
        'accounts.AccountChart', on_delete=models.PROTECT,
        related_name='purchase_request_category',
        help_text='The single AccountChart row this category resolves to',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Inactive categories are kept (for historical requests) but cannot be selected for new ones',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchaserequestcategory'
        verbose_name_plural = 'Purchase request categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseRequestAttachment(models.Model):
    """
    File attachment on a purchase request.

    Supports the paper form's instruction:
    'Please attach detailed specifications for the requirement.'
    """

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(
        upload_to='procurement/purchase-requests/attachments/',
    )
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        'hr.Employees', on_delete=models.PROTECT,
        related_name='pr_attachments',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_purchaserequestattachment'

    def __str__(self):
        return self.original_filename


class PurchaseRequestDecision(models.Model):
    """
    Immutable decision record for the purchase request approval workflow
    (Section C of the paper form).

    Each approval/rejection is stored as a separate record so that
    decision history is never overwritten.
    """

    STAGE_CHOICES = [
        ('DEPARTMENT_HEAD', 'Department Head'),
        ('ACCOUNTS', 'Accounts'),
        ('GM', 'General Manager'),
        ('DIRECTOR', 'Director'),
    ]

    DECISION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('VERIFIED', 'Verified'),
        ('RECOMMENDED', 'Recommended'),
        ('REJECTED', 'Rejected'),
    ]

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='decisions',
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    actor = models.ForeignKey(
        'hr.Employees', on_delete=models.PROTECT,
        related_name='pr_decisions',
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_purchaserequestdecision'
        indexes = [
            models.Index(
                fields=['purchase_request'], name='prd_purchase_request_idx',
            ),
            models.Index(fields=['stage'], name='prd_stage_idx'),
        ]

    def __str__(self):
        return f"{self.get_stage_display()} – {self.get_decision_display()}"


class PurchaseOrder(models.Model):
    """Purchase order created from approved purchase request."""
    purchase_request = models.OneToOneField(
        PurchaseRequest,
        on_delete=models.CASCADE,
        null=True, # Review when we get to PO integration; may want to enforce non-null
        related_name='purchase_order'
    )
    order_number = models.CharField(max_length=100, unique=True)
    approved_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)

    class Meta:
        db_table = 'procurement_purchaseorder'

    def __str__(self):
        return self.order_number


class FuelRequisition(models.Model):
    STATUS_CHOICES = [
        ('PENDING_DEPARTMENT', 'Pending Department'),
        ('PENDING_RECIPIENT', 'Pending Recipient / Driver'),
        ('PENDING_FINANCE', 'Pending Finance / General Manager'),
        ('PENDING_DIRECTOR', 'Pending Director'),
        ('PENDING_ADMIN', 'Pending Administration'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='fuel_requisitions')
    department = models.ForeignKey('hr.Department', on_delete=models.PROTECT)
    programme = models.CharField(max_length=255, blank=True)
    recipient_driver = models.CharField(max_length=255)
    requester_signature = models.CharField(max_length=255, blank=True)
    vehicle_registration = models.CharField(max_length=50)
    request_date = models.DateField(default=timezone.now)
    diesel_quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    diesel_quantity_words = models.CharField(max_length=255, blank=True)
    petrol_quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    petrol_quantity_words = models.CharField(max_length=255, blank=True)
    purpose = models.TextField()
    destination = models.CharField(max_length=255)
    destination_dates = models.CharField(max_length=255, blank=True)
    finance_recommendation = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_DEPARTMENT')
    rejection_reason = models.TextField(blank=True)
    department_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='department_fuel_approvals')
    department_approved_at = models.DateTimeField(null=True, blank=True)
    recipient_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='recipient_fuel_approvals')
    recipient_approved_at = models.DateTimeField(null=True, blank=True)
    finance_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='finance_fuel_approvals')
    finance_approved_at = models.DateTimeField(null=True, blank=True)
    director_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='director_fuel_approvals')
    director_approved_at = models.DateTimeField(null=True, blank=True)
    admin_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='admin_fuel_approvals')
    admin_approved_at = models.DateTimeField(null=True, blank=True)
    issuance_quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    serial_numbers = models.CharField(max_length=255, blank=True)
    issued_by_name = models.CharField(max_length=255, blank=True)
    received_by_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class StoresRequisition(models.Model):
    """Stores requisition copied from the paper form and routed for approval."""

    STATUS_CHOICES = [
        ('PENDING_DEPARTMENT', 'Pending Head of Department'),
        ('PENDING_PROCUREMENT', 'Pending Procurement'),
        ('PENDING_ACCOUNTS', 'Pending Accounts'),
        ('PENDING_GENERAL_MANAGER', 'Pending General Manager'),
        ('PENDING_DIRECTOR', 'Pending Director'),
        ('PENDING_ADMIN', 'Pending Admin'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stores_requisitions')
    department = models.ForeignKey('hr.Department', on_delete=models.PROTECT)
    requisition_number = models.CharField(max_length=30, unique=True, blank=True)
    items = models.JSONField(default=list)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_DEPARTMENT')
    rejection_reason = models.TextField(blank=True)
    department_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='department_stores_approvals')
    department_approved_at = models.DateTimeField(null=True, blank=True)
    procurement_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='procurement_stores_approvals')
    procurement_approved_at = models.DateTimeField(null=True, blank=True)
    accounts_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='accounts_stores_approvals')
    accounts_approved_at = models.DateTimeField(null=True, blank=True)
    general_manager_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='general_manager_stores_approvals')
    general_manager_approved_at = models.DateTimeField(null=True, blank=True)
    director_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='director_stores_approvals')
    director_approved_at = models.DateTimeField(null=True, blank=True)
    admin_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='admin_stores_approvals')
    admin_approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            super().save(*args, **kwargs)
            self.requisition_number = f'SR-{self.pk:05d}'
            return super().save(update_fields=['requisition_number'])
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class ComparativeSchedule(models.Model):
    """Comparative schedule for quotations with a fixed approval route."""

    STATUS_CHOICES = [
        ('PENDING_DIRECTOR', 'Pending Director'),
        ('PENDING_PROCUREMENT', 'Pending Procurement'),
        ('PENDING_ACCOUNTS', 'Pending Accounts'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='comparative_schedules')
    schedule_number = models.CharField(max_length=30, unique=True, blank=True)
    compliance = models.JSONField(default=dict)
    items = models.JSONField(default=list)
    recommendation = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_DIRECTOR')
    rejection_reason = models.TextField(blank=True)
    procurement_submitted_at = models.DateTimeField(auto_now_add=True)
    director_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='director_comparative_approvals')
    director_approved_at = models.DateTimeField(null=True, blank=True)
    procurement_finalised_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='final_procurement_comparative_approvals')
    procurement_finalised_at = models.DateTimeField(null=True, blank=True)
    accounts_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='accounts_comparative_approvals')
    accounts_approved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.schedule_number:
            super().save(*args, **kwargs)
            self.schedule_number = f'CS-{self.pk:05d}'
            return super().save(update_fields=['schedule_number'])
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['-procurement_submitted_at']

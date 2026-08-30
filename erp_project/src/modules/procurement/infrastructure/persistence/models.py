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
    """Purchase request for procurement workflow."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('LEVEL1_APPROVED', 'Level 1 Approved'),
        ('LEVEL2_APPROVED', 'Level 2 Approved'),
        ('REJECTED', 'Rejected'),
    ]

    requester = models.CharField(max_length=255)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    budget_center = models.ForeignKey(BudgetCenter, on_delete=models.CASCADE)
    items = models.ManyToManyField(InventoryItem, through='PurchaseRequestItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_purchaserequest'

    def __str__(self):
        return f"PR-{self.id} by {self.requester}"


class PurchaseRequestItem(models.Model):
    """Line item in a purchase request."""
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='request_items'
    )
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        db_table = 'procurement_purchaserequestitem'

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


class PurchaseOrder(models.Model):
    """Purchase order created from approved purchase request."""
    purchase_request = models.OneToOneField(
        PurchaseRequest,
        on_delete=models.CASCADE,
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

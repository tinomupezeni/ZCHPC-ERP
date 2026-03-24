"""
Django models for the Procurement module.
"""
from django.db import models


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

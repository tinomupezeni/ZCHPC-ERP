from django.db import models
from .vendor import Vendor
from .inventory_item import InventoryItem
from .budget_center import BudgetCenter

class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('LEVEL1_APPROVED', 'Level 1 Approved'),
        ('LEVEL2_APPROVED', 'Level 2 Approved'),
        ('REJECTED', 'Rejected')
    ]

    requester = models.CharField(max_length=255)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    budget_center = models.ForeignKey(BudgetCenter, on_delete=models.CASCADE)
    items = models.ManyToManyField(InventoryItem, through='PurchaseRequestItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PurchaseRequestItem(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()

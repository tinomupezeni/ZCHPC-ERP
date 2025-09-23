from django.db import models
from .purchase_request import PurchaseRequest

class PurchaseOrder(models.Model):
    purchase_request = models.OneToOneField(PurchaseRequest, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=100, unique=True)
    approved_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)

    def __str__(self):
        return self.order_number

from django.db import models

class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    quantity = models.IntegerField(default=0)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.name

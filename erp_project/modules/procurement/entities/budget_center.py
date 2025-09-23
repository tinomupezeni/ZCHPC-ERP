from django.db import models

class BudgetCenter(models.Model):
    name = models.CharField(max_length=255)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    used_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def remaining_amount(self):
        return self.allocated_amount - self.used_amount

    def __str__(self):
        return self.name

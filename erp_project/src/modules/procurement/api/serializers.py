"""
API serializers for the procurement module.
"""

from rest_framework import serializers


# ============================
# Supplier Serializers
# ============================

class SupplierSerializer(serializers.Serializer):
    """Serializer for supplier display."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    is_active = serializers.BooleanField()


class CreateSupplierSerializer(serializers.Serializer):
    """Serializer for creating a supplier."""

    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)


class UpdateSupplierSerializer(serializers.Serializer):
    """Serializer for updating a supplier."""

    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=50, required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)
    rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, required=False
    )


# ============================
# Inventory Item Serializers
# ============================

class InventoryItemSerializer(serializers.Serializer):
    """Serializer for inventory item display."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    sku = serializers.CharField()
    quantity = serializers.IntegerField()
    price_per_unit = serializers.DecimalField(max_digits=12, decimal_places=2)
    reorder_level = serializers.IntegerField()
    is_active = serializers.BooleanField()
    needs_reorder = serializers.BooleanField(read_only=True)


class CreateInventoryItemSerializer(serializers.Serializer):
    """Serializer for creating an inventory item."""

    name = serializers.CharField(max_length=255)
    sku = serializers.CharField(max_length=50)
    quantity = serializers.IntegerField(default=0, min_value=0)
    price_per_unit = serializers.DecimalField(max_digits=12, decimal_places=2)
    reorder_level = serializers.IntegerField(default=0, min_value=0)


class UpdateInventoryItemSerializer(serializers.Serializer):
    """Serializer for updating an inventory item."""

    name = serializers.CharField(max_length=255, required=False)
    quantity = serializers.IntegerField(min_value=0, required=False)
    price_per_unit = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    reorder_level = serializers.IntegerField(min_value=0, required=False)


# ============================
# Budget Center Serializers
# ============================

class BudgetCenterSerializer(serializers.Serializer):
    """Serializer for budget center display."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    code = serializers.CharField()
    allocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    used_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    fiscal_year = serializers.IntegerField()
    is_active = serializers.BooleanField()


class CreateBudgetCenterSerializer(serializers.Serializer):
    """Serializer for creating a budget center."""

    name = serializers.CharField(max_length=255)
    allocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    fiscal_year = serializers.IntegerField(required=False)


class UpdateBudgetCenterSerializer(serializers.Serializer):
    """Serializer for updating a budget center."""

    name = serializers.CharField(max_length=255, required=False)
    allocated_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )


# ============================
# Purchase Order Serializers
# ============================

class PurchaseOrderSerializer(serializers.Serializer):
    """Serializer for purchase order display."""

    id = serializers.IntegerField(read_only=True)
    order_number = serializers.CharField()
    request_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.CharField()
    delivered = serializers.BooleanField()
    notes = serializers.CharField(allow_null=True)


class MarkDeliveredSerializer(serializers.Serializer):
    """Serializer for marking goods as delivered."""

    is_partial = serializers.BooleanField(default=False)


class CancelOrderSerializer(serializers.Serializer):
    """Serializer for cancelling an order."""

    reason = serializers.CharField(required=False, allow_null=True)

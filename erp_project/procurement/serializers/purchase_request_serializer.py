from rest_framework import serializers
from ..entities.purchase_request import PurchaseRequest, PurchaseRequestItem

class PurchaseRequestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequestItem
        fields = ['item', 'quantity']

class PurchaseRequestSerializer(serializers.ModelSerializer):
    items = PurchaseRequestItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = ['id', 'requester', 'vendor', 'items', 'total_amount', 'status', 'created_at']

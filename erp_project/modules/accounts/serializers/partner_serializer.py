# serializers/partner_serializer.py
from rest_framework import serializers
from ..accounts_models import Partner, Currency

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'name', 'code', 'symbol', 'rate_to_base', 'created_at', 'updated_at']


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'partner_type', 'vat_number', 'currency', 'created_at', 'updated_at']

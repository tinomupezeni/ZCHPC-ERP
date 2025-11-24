# serializers/account_chart_serializer.py
from rest_framework import serializers
from ..accounts_models import AccountChart

class AccountChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountChart
        fields = ['id', 'code', 'name', 'parent', 'account_type', 'reconcile', 'currency', 'created_at', 'updated_at']

# serializers/analytic_serializer.py
from rest_framework import serializers
from ..accounts_models import AnalyticAccount, AccountTag

class AnalyticAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticAccount
        fields = ['id', 'name', 'code', 'parent', 'created_at', 'updated_at']


class AccountTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountTag
        fields = ['id', 'name', 'color', 'created_at', 'updated_at']

# serializers/reporting_serializer.py
from rest_framework import serializers

class TrialBalanceSerializer(serializers.Serializer):
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance = serializers.DecimalField(max_digits=18, decimal_places=2)


class ProfitLossSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=18, decimal_places=2)


class BalanceSheetSerializer(serializers.Serializer):
    assets = serializers.DecimalField(max_digits=18, decimal_places=2)
    liabilities = serializers.DecimalField(max_digits=18, decimal_places=2)
    equity = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance_check = serializers.DecimalField(max_digits=18, decimal_places=2)


class AnalyticReportSerializer(serializers.Serializer):
    account__code = serializers.CharField()
    account__name = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance = serializers.DecimalField(max_digits=18, decimal_places=2)

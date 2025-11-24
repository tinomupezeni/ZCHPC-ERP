# services/reporting_service.py
from django.db.models import Sum, F
from ..accounts_models import AccountMoveLine, AccountChart, AnalyticAccount, AccountTag
from decimal import Decimal

class ReportingService:

    @staticmethod
    def trial_balance():
        """
        Returns a trial balance: debit, credit, balance per account
        """
        accounts = AccountChart.objects.all()
        result = []

        for account in accounts:
            lines = AccountMoveLine.objects.filter(account=account, move__posted=True)
            total_debit = lines.aggregate(total=Sum('debit'))['total'] or Decimal(0)
            total_credit = lines.aggregate(total=Sum('credit'))['total'] or Decimal(0)
            balance = total_debit - total_credit
            result.append({
                'account_code': account.code,
                'account_name': account.name,
                'debit': total_debit,
                'credit': total_credit,
                'balance': balance
            })
        return result

    @staticmethod
    def profit_and_loss(start_date=None, end_date=None):
        """
        Generate P&L by account_type = revenue/expense
        """
        lines = AccountMoveLine.objects.filter(move__posted=True)
        if start_date:
            lines = lines.filter(date__gte=start_date)
        if end_date:
            lines = lines.filter(date__lte=end_date)

        revenue_accounts = AccountChart.objects.filter(account_type='regular', code__startswith='4')  # example: 4xx revenue
        expense_accounts = AccountChart.objects.filter(account_type='regular', code__startswith='5')  # example: 5xx expenses

        revenue = lines.filter(account__in=revenue_accounts).aggregate(debit_sum=Sum('debit'), credit_sum=Sum('credit'))
        expense = lines.filter(account__in=expense_accounts).aggregate(debit_sum=Sum('debit'), credit_sum=Sum('credit'))

        total_revenue = (revenue['credit_sum'] or 0) - (revenue['debit_sum'] or 0)
        total_expense = (expense['debit_sum'] or 0) - (expense['credit_sum'] or 0)
        net_profit = total_revenue - total_expense

        return {
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'net_profit': net_profit
        }

    @staticmethod
    def balance_sheet():
        """
        Generate balance sheet using account type grouping: assets, liabilities, equity
        """
        lines = AccountMoveLine.objects.filter(move__posted=True)
        assets = AccountChart.objects.filter(account_type='regular', code__startswith='1')
        liabilities = AccountChart.objects.filter(account_type='regular', code__startswith='2')
        equity = AccountChart.objects.filter(account_type='regular', code__startswith='3')

        def aggregate_balance(accounts_queryset):
            total = Decimal(0)
            for acc in accounts_queryset:
                acc_lines = lines.filter(account=acc)
                total_debit = acc_lines.aggregate(total=Sum('debit'))['total'] or Decimal(0)
                total_credit = acc_lines.aggregate(total=Sum('credit'))['total'] or Decimal(0)
                total += total_debit - total_credit
            return total

        return {
            'assets': aggregate_balance(assets),
            'liabilities': aggregate_balance(liabilities),
            'equity': aggregate_balance(equity),
            'balance_check': aggregate_balance(assets) - (aggregate_balance(liabilities) + aggregate_balance(equity))
        }

    @staticmethod
    def analytic_report(analytic_account_id=None, tag_id=None):
        """
        Multi-dimensional analysis based on analytic accounts or tags
        """
        lines = AccountMoveLine.objects.filter(move__posted=True)
        if analytic_account_id:
            lines = lines.filter(analytic_account_id=analytic_account_id)
        if tag_id:
            lines = lines.filter(tag_ids__contains=[tag_id])

        result = lines.values('account__code', 'account__name') \
            .annotate(debit=Sum('debit'), credit=Sum('credit'), balance=F('debit') - F('credit')) \
            .order_by('account__code')

        return list(result)

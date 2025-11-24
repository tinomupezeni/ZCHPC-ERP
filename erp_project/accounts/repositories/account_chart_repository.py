# repositories/account_chart_repository.py
from ..accounts_modelsaccounts_models import AccountChart

class AccountChartRepository:
    @staticmethod
    def get_all():
        return AccountChart.objects.all()

    @staticmethod
    def get_by_id(account_id):
        return AccountChart.objects.get(id=account_id)

    @staticmethod
    def create(**kwargs):
        return AccountChart.objects.create(**kwargs)

    @staticmethod
    def update(account_id, **kwargs):
        account = AccountChart.objects.get(id=account_id)
        for key, value in kwargs.items():
            setattr(account, key, value)
        account.save()
        return account

    @staticmethod
    def delete(account_id):
        account = AccountChart.objects.get(id=account_id)
        account.delete()

# repositories/analytic_repository.py
from ..accounts_models import AnalyticAccount, AccountTag

class AnalyticAccountRepository:
    @staticmethod
    def get_all():
        return AnalyticAccount.objects.all()

    @staticmethod
    def get_by_id(account_id):
        return AnalyticAccount.objects.get(id=account_id)

    @staticmethod
    def create(**kwargs):
        return AnalyticAccount.objects.create(**kwargs)

    @staticmethod
    def update(account_id, **kwargs):
        account = AnalyticAccount.objects.get(id=account_id)
        for key, value in kwargs.items():
            setattr(account, key, value)
        account.save()
        return account

    @staticmethod
    def delete(account_id):
        account = AnalyticAccount.objects.get(id=account_id)
        account.delete()


class AccountTagRepository:
    @staticmethod
    def get_all():
        return AccountTag.objects.all()

    @staticmethod
    def get_by_id(tag_id):
        return AccountTag.objects.get(id=tag_id)

    @staticmethod
    def create(**kwargs):
        return AccountTag.objects.create(**kwargs)

    @staticmethod
    def update(tag_id, **kwargs):
        tag = AccountTag.objects.get(id=tag_id)
        for key, value in kwargs.items():
            setattr(tag, key, value)
        tag.save()
        return tag

    @staticmethod
    def delete(tag_id):
        tag = AccountTag.objects.get(id=tag_id)
        tag.delete()

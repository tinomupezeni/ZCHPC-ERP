# services/analytic_service.py
from accounts.repositories.analytic_repository import AnalyticAccountRepository, AccountTagRepository

class AnalyticAccountService:
    @staticmethod
    def create_account(data):
        if data.get('parent') == data.get('id'):
            raise ValueError("Analytic Account cannot be its own parent")
        return AnalyticAccountRepository.create(**data)

    @staticmethod
    def update_account(account_id, data):
        return AnalyticAccountRepository.update(account_id, data)

    @staticmethod
    def delete_account(account_id):
        return AnalyticAccountRepository.delete(account_id)


class AccountTagService:
    @staticmethod
    def create_tag(data):
        return AccountTagRepository.create(**data)

    @staticmethod
    def update_tag(tag_id, data):
        return AccountTagRepository.update(tag_id, data)

    @staticmethod
    def delete_tag(tag_id):
        return AccountTagRepository.delete(tag_id)

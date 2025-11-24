# services/account_chart_service.py
from accounts.repositories.account_chart_repository import AccountChartRepository

class AccountChartService:
    @staticmethod
    def create_account(data):
        # Example validation: cannot have parent as self
        if data.get('parent') == data.get('id'):
            raise ValueError("Account cannot be its own parent")
        return AccountChartRepository.create(**data)

    @staticmethod
    def update_account(account_id, data):
        return AccountChartRepository.update(account_id, **data)

    @staticmethod
    def delete_account(account_id):
        return AccountChartRepository.delete(account_id)

# services/partner_service.py
from accounts.repositories.partner_repository import PartnerRepository, CurrencyRepository

class PartnerService:
    @staticmethod
    def create_partner(data):
        return PartnerRepository.create(**data)

    @staticmethod
    def update_partner(partner_id, data):
        return PartnerRepository.update(partner_id, data)

    @staticmethod
    def delete_partner(partner_id):
        return PartnerRepository.delete(partner_id)


class CurrencyService:
    @staticmethod
    def create_currency(data):
        return CurrencyRepository.create(**data)

    @staticmethod
    def update_currency(currency_id, data):
        return CurrencyRepository.update(currency_id, data)

    @staticmethod
    def delete_currency(currency_id):
        return CurrencyRepository.delete(currency_id)

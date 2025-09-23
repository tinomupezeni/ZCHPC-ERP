# repositories/partner_repository.py
from ..accounts_models import Partner, Currency

class PartnerRepository:
    @staticmethod
    def get_all():
        return Partner.objects.all()

    @staticmethod
    def get_by_id(partner_id):
        return Partner.objects.get(id=partner_id)

    @staticmethod
    def create(**kwargs):
        return Partner.objects.create(**kwargs)

    @staticmethod
    def update(partner_id, **kwargs):
        partner = Partner.objects.get(id=partner_id)
        for key, value in kwargs.items():
            setattr(partner, key, value)
        partner.save()
        return partner

    @staticmethod
    def delete(partner_id):
        partner = Partner.objects.get(id=partner_id)
        partner.delete()


class CurrencyRepository:
    @staticmethod
    def get_all():
        return Currency.objects.all()

    @staticmethod
    def get_by_id(currency_id):
        return Currency.objects.get(id=currency_id)

    @staticmethod
    def create(**kwargs):
        return Currency.objects.create(**kwargs)

    @staticmethod
    def update(currency_id, **kwargs):
        currency = Currency.objects.get(id=currency_id)
        for key, value in kwargs.items():
            setattr(currency, key, value)
        currency.save()
        return currency

    @staticmethod
    def delete(currency_id):
        currency = Currency.objects.get(id=currency_id)
        currency.delete()

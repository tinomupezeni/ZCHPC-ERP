# views/partner_views.py
from rest_framework import viewsets
from rest_framework.response import Response
from ..accounts_models import Partner, Currency
from accounts.serializers.partner_serializer import PartnerSerializer, CurrencySerializer
from accounts.services.partner_service import PartnerService, CurrencyService

class PartnerViewSet(viewsets.ViewSet):
    def list(self, request):
        partners = Partner.objects.all()
        serializer = PartnerSerializer(partners, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        partner = Partner.objects.get(id=pk)
        serializer = PartnerSerializer(partner)
        return Response(serializer.data)

    def create(self, request):
        partner = PartnerService.create_partner(request.data)
        serializer = PartnerSerializer(partner)
        return Response(serializer.data)

    def update(self, request, pk=None):
        partner = PartnerService.update_partner(pk, request.data)
        serializer = PartnerSerializer(partner)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        PartnerService.delete_partner(pk)
        return Response(status=204)


class CurrencyViewSet(viewsets.ViewSet):
    def list(self, request):
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        currency = Currency.objects.get(id=pk)
        serializer = CurrencySerializer(currency)
        return Response(serializer.data)

    def create(self, request):
        currency = CurrencyService.create_currency(request.data)
        serializer = CurrencySerializer(currency)
        return Response(serializer.data)

    def update(self, request, pk=None):
        currency = CurrencyService.update_currency(pk, request.data)
        serializer = CurrencySerializer(currency)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        CurrencyService.delete_currency(pk)
        return Response(status=204)

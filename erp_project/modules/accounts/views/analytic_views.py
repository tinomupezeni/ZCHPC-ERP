# views/analytic_views.py
from rest_framework import viewsets
from rest_framework.response import Response
from ..accounts_models import AnalyticAccount, AccountTag
from accounts.serializers.analytic_serializer import AnalyticAccountSerializer, AccountTagSerializer
from accounts.services.analytic_service import AnalyticAccountService, AccountTagService

class AnalyticAccountViewSet(viewsets.ViewSet):
    def list(self, request):
        accounts = AnalyticAccount.objects.all()
        serializer = AnalyticAccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        account = AnalyticAccount.objects.get(id=pk)
        serializer = AnalyticAccountSerializer(account)
        return Response(serializer.data)

    def create(self, request):
        account = AnalyticAccountService.create_account(request.data)
        serializer = AnalyticAccountSerializer(account)
        return Response(serializer.data)

    def update(self, request, pk=None):
        account = AnalyticAccountService.update_account(pk, request.data)
        serializer = AnalyticAccountSerializer(account)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        AnalyticAccountService.delete_account(pk)
        return Response(status=204)


class AccountTagViewSet(viewsets.ViewSet):
    def list(self, request):
        tags = AccountTag.objects.all()
        serializer = AccountTagSerializer(tags, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        tag = AccountTag.objects.get(id=pk)
        serializer = AccountTagSerializer(tag)
        return Response(serializer.data)

    def create(self, request):
        tag = AccountTagService.create_tag(request.data)
        serializer = AccountTagSerializer(tag)
        return Response(serializer.data)

    def update(self, request, pk=None):
        tag = AccountTagService.update_tag(pk, request.data)
        serializer = AccountTagSerializer(tag)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        AccountTagService.delete_tag(pk)
        return Response(status=204)

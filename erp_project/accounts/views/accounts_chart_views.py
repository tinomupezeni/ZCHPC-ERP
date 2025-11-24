# views/account_chart_view.py
from rest_framework import viewsets
from ..accounts_models import AccountChart
from accounts.serializers.account_chart_serializer import AccountChartSerializer
from accounts.services.account_chart_service import AccountChartService
from rest_framework.response import Response
from rest_framework import status

class AccountChartViewSet(viewsets.ViewSet):

    def list(self, request):
        accounts = AccountChart.objects.all()
        serializer = AccountChartSerializer(accounts, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        account = AccountChart.objects.get(id=pk)
        serializer = AccountChartSerializer(account)
        return Response(serializer.data)

    def create(self, request):
        data = request.data
        account = AccountChartService.create_account(data)
        serializer = AccountChartSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        data = request.data
        account = AccountChartService.update_account(pk, data)
        serializer = AccountChartSerializer(account)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        AccountChartService.delete_account(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

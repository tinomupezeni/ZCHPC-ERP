# views/reporting_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.services.reporting_service import ReportingService
from accounts.serializers.reporting_serializer import TrialBalanceSerializer, ProfitLossSerializer, BalanceSheetSerializer, AnalyticReportSerializer

class TrialBalanceView(APIView):
    def get(self, request):
        data = ReportingService.trial_balance()
        serializer = TrialBalanceSerializer(data, many=True)
        return Response(serializer.data)


class ProfitLossView(APIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        data = ReportingService.profit_and_loss(start_date, end_date)
        serializer = ProfitLossSerializer(data)
        return Response(serializer.data)


class BalanceSheetView(APIView):
    def get(self, request):
        data = ReportingService.balance_sheet()
        serializer = BalanceSheetSerializer(data)
        return Response(serializer.data)


class AnalyticReportView(APIView):
    def get(self, request):
        analytic_id = request.query_params.get('analytic_account_id')
        tag_id = request.query_params.get('tag_id')
        data = ReportingService.analytic_report(analytic_id, tag_id)
        serializer = AnalyticReportSerializer(data, many=True)
        return Response(serializer.data)

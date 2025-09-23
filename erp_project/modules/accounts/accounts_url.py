# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.accounts_chart_views import AccountChartViewSet
from .views.account_move_view import AccountMoveViewSet
from .views.analytic_views import AnalyticAccountViewSet, AccountTagViewSet
from .views.partner_views import PartnerViewSet, CurrencyViewSet
from .views.reporting_views import TrialBalanceView, ProfitLossView, BalanceSheetView, AnalyticReportView

router = DefaultRouter()
router.register(r'accounts', AccountChartViewSet, basename='accounts')
router.register(r'moves', AccountMoveViewSet, basename='moves')
router.register(r'analytic-accounts', AnalyticAccountViewSet, basename='analytic-accounts')
router.register(r'account-tags', AccountTagViewSet, basename='account-tags')
router.register(r'partners', PartnerViewSet, basename='partners')
router.register(r'currencies', CurrencyViewSet, basename='currencies')


urlpatterns = [
    path('', include(router.urls)),
    path('reports/trial-balance/', TrialBalanceView.as_view(), name='trial-balance'),
    path('reports/profit-loss/', ProfitLossView.as_view(), name='profit-loss'),
    path('reports/balance-sheet/', BalanceSheetView.as_view(), name='balance-sheet'),
    path('reports/analytic/', AnalyticReportView.as_view(), name='analytic-report'),
]

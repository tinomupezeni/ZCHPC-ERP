# erp/urls.py
from rest_framework.routers import DefaultRouter
from .payroll_views import PayrollViewSet, CurrencyRateViewSet

app_name = 'payroll'

router = DefaultRouter()
router.register(r'payrolls', PayrollViewSet, basename='payroll')
router.register(r'rates', CurrencyRateViewSet, basename='currency-rate')

urlpatterns = router.urls

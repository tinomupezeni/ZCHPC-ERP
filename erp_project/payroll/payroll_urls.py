# erp/urls.py
from rest_framework.routers import DefaultRouter
from .payroll_views import PayrollViewSet

router = DefaultRouter()
router.register(r'payrolls', PayrollViewSet, basename='payroll')

urlpatterns = router.urls

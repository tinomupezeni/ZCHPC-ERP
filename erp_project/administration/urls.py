from django.urls import path
from .views import AdminDashboardView

urlpatterns = [
    # Creates the .../api/admin/dashboard/ endpoint
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
]
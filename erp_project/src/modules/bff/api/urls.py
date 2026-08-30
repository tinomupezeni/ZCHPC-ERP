from django.urls import path
from .views import BFFEmployeeDetailView

app_name = "bff"

urlpatterns = [
    path("employees/<uuid:uuid>/", BFFEmployeeDetailView.as_view(), name="employee-detail"),
]

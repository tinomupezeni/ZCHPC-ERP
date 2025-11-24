from django.urls import path, include

from .view.audit_view import AuditLogListView

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import  TokenRefreshView
from .view.user_views import CustomUserViewSet  # 1. Import your new User ViewSet
from .view.auth_view import CustomTokenObtainPairView


router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')  # 2. Register the User ViewSet


urlpatterns = [
    path('', include(router.urls)),

    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),



    # System logs
    path("logs/", AuditLogListView.as_view(), name="audit-log-list"),
  
    

]

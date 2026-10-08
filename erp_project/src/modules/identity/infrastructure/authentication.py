"""
Custom authentication backends for the Identity module.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authentication backend that allows users to log in using their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    def user_can_authenticate(self, user):
        """Also refuse a login whose employee is not in active employment (AUD-02)."""
        from modules.identity.infrastructure.account_access import employment_allows_access

        return super().user_can_authenticate(user) and employment_allows_access(user)

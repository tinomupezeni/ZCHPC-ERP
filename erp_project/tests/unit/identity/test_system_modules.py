import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from modules.identity.infrastructure.persistence.models import SystemModule, CustomUser

@pytest.mark.django_db
class TestSystemModules:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.client = APIClient()
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Clear existing modules from seed if any
        SystemModule.objects.all().delete()
        
        # Create modules
        self.hr_module = SystemModule.objects.create(
            identifier='hr',
            name='Human Resources',
            is_active=True
        )
        self.payroll_module = SystemModule.objects.create(
            identifier='payroll',
            name='Payroll',
            is_active=False
        )

    def test_list_active_modules(self):
        url = reverse('identity:system-module-active-modules')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        active_identifiers = [m['identifier'] for m in response.data]
        assert 'hr' in active_identifiers
        assert 'payroll' not in active_identifiers

    def test_install_module(self):
        url = reverse('identity:system-module-install', kwargs={'identifier': 'payroll'})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True
        
        self.payroll_module.refresh_from_db()
        assert self.payroll_module.is_active is True

    def test_middleware_blocks_inactive_module(self):
        # We need an endpoint in payroll to test this
        url = '/api/v2/payroll/'
        response = self.client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "not installed" in data['detail']

    def test_middleware_allows_active_module(self):
        url = '/api/v2/hr/'
        response = self.client.get(url)
        # Should not be 403 from ModuleAccessMiddleware
        assert response.status_code != status.HTTP_403_FORBIDDEN
        # It might be 404 if the exact path /api/v2/hr/ isn't registered (usually it's /api/v2/hr/employees/ etc)
        # but 403 is what we are checking for.

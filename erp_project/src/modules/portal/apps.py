from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.portal'
    label = 'portal'
    verbose_name = 'Employee Portal'

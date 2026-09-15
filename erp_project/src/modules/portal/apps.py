from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.portal'
    label = 'portal'
    verbose_name = 'Employee Portal'

    def ready(self):
        # Subscribe to cross-module domain events (Slice 3 notifications) -
        # see event_handlers.py.
        from . import event_handlers
        event_handlers.register()

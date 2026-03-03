from django.apps import AppConfig
from django.db.models.signals import post_migrate

class HumanResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'human_resources'

    def ready(self):
        # Import the function here to avoid AppRegistryNotReady errors
        from .signals import create_default_roles
        post_migrate.connect(create_default_roles, sender=self)

        # Import signals module to register all signal handlers
        # This ensures the @receiver decorators are processed
        from . import signals  # noqa: F401
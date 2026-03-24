from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.hr'
    label = 'hr'
    verbose_name = 'Human Resources'

    def ready(self):
        # Import signals
        from . import signals  # noqa

# authentication/apps.py

from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    
    # This line tells Django your app's name
    name = 'authentication'
    
    # This line tells Django to load the models from the correct file
    label = 'authentication'
    models_module = 'authentication.auth_models'
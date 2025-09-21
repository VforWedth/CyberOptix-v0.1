from django.apps import AppConfig


class FlameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flame'

    def ready(self):
        import flame.signals

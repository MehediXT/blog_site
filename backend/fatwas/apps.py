from django.apps import AppConfig


class FatwasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fatwas'

    def ready(self):
        import fatwas.signals  # noqa: F401


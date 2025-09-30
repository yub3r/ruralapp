from django.apps import AppConfig


class RuralappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ruralapp'
    verbose_name = 'RURALAPP'

    def ready(self):
        # Importa señales para sincronizar Membership ↔ Groups
        from . import signals  # noqa: F401

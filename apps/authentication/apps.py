from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    verbose_name = "Authentication"

    def ready(self) -> None:
        from apps.authentication.infrastructure.factory import (
            register_authentication_event_handlers,
        )

        register_authentication_event_handlers()

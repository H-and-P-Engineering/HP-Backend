from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.infrastructure.users"
    verbose_name = "Users"

    def ready(self) -> None:
        from .factory import register_user_event_handlers

        register_user_event_handlers()


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.infrastructure.authentication"
    verbose_name = "Authentication"

    def ready(self) -> None:
        from .factory import register_authentication_event_handlers

        register_authentication_event_handlers()


class BusinessVerificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.infrastructure.business_verification"
    verbose_name = "Business Verification"

    def ready(self) -> None:
        from .factory import register_business_verification_event_handlers

        register_business_verification_event_handlers()


class LocationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.infrastructure.location"
    verbose_name = "Location"

    def ready(self) -> None:
        from .factory import register_location_event_handlers

        register_location_event_handlers()

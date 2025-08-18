from django.apps import AppConfig


class BusinessVerificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.business_verification"
    verbose_name = "Business Verification"

    def ready(self) -> None:
        from apps.business_verification.infrastructure.factory import (
            register_business_verification_event_handlers,
        )

        register_business_verification_event_handlers()

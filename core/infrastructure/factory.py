from core.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoVerificationServiceAdapter,
)


def get_verification_service():
    return DjangoVerificationServiceAdapter()


def get_cache_service():
    return DjangoCacheServiceAdapter()


def get_email_service():
    return DjangoEmailServiceAdapter()

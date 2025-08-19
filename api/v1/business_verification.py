from django.urls import path

from app.presentation.views.business_verification import (
    create_business_profile,
    get_business_verification_status,
    verify_business,
    verify_business_email,
    verify_business_email_request,
)

app_name = "business_verification"

urlpatterns = [
    path(
        "create-business-profile/",
        create_business_profile,
        name="create-business-profile",
    ),
    path(
        "verify-business/",
        verify_business,
        name="verify-business",
    ),
    path(
        "business-verification-status/",
        get_business_verification_status,
        name="business-verification-status",
    ),
    path(
        "verify-business-email/<str:verification_uuid>/<str:verification_token>/",
        verify_business_email,
        name="verify-business-email",
    ),
    path(
        "verify-business-email/request/",
        verify_business_email_request,
        name="verify-business-email-request",
    ),
]

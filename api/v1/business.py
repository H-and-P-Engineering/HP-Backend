from django.urls import path

from business import views

app_name = "business"

urlpatterns = [
    path("profile/", views.create_business_profile, name="create-business-profile"),
    path("verify/", views.verify_business, name="verify-business"),
    path(
        "verification-status/",
        views.get_business_verification_status,
        name="business-verification-status",
    ),
    path(
        "verify-email/<uuid:user_uuid>/<str:verification_token>/",
        views.verify_business_email,
        name="verify-business-email",
    ),
    path(
        "verify-email/request/",
        views.request_business_email_verification,
        name="request-business-email-verification",
    ),
]

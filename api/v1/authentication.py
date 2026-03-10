from django.urls import path, URLPattern
from social_django.urls import extra

from users.views import (
    register_user,
    request_email_verification,
    verify_email,
    login_user,
    logout_user,
    begin_social_authentication,
    complete_social_authentication,
    get_social_auth_data,
)

app_name = "authentication"

urlpatterns: list[URLPattern] = [
    path("register/", register_user, name="register"),
    path(
        "verify-email/request/",
        request_email_verification,
        name="request-email-verification",
    ),
    path(
        "verify-email/<uuid:user_uuid>/<str:verification_token>/",
        verify_email,
        name="verify-email",
    ),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path(
        f"social/begin/<str:backend>{extra}",
        begin_social_authentication,
        name="social-begin",
    ),
    path(
        "social/complete/<str:backend>/",
        complete_social_authentication,
        name="social-complete",
    ),
    path(
        "social/data/",
        get_social_auth_data,
        name="social-data",
    ),
]

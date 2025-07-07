from django.urls import path
from social_django.urls import extra

from apps.authentication.presentation.views import (
    begin_social_authentication,
    complete_social_authentication,
    login_user,
    logout_user,
    register_user,
    verify_email,
    verify_email_request,
)

app_name = "authentication"

urlpatterns = [
    path("register/", register_user, name="register"),
    path("verify-email/request/", verify_email_request, name="verify-email-request"),
    path(
        "verify-email/<str:user_uuid>/<str:verification_token>/",
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
]

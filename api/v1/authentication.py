from django.urls import path
from social_django.urls import extra

from apps.authentication.presentation.views import (
    begin_social_authentication,
    complete_social_authentication,
    get_social_auth_data,
    login_user,
    logout_user,
    register_user,
    update_user_type,
    verify_email,
    verify_email_request,
)

app_name = "authentication"

urlpatterns = [
    path("register/", register_user, name="register"),
    path("update-user-type/", update_user_type, name="update-user-type"),
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
    path("social/data/", get_social_auth_data, name="social-data"),
]

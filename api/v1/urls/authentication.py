"""v1 Authentication urls."""

from django.urls import path
from social_django.urls import extra

from apps.authentication.views import (
    EmailVerificationView,
    LoginView,
    RegisterView,
    SocialAuthenticationBeginView,
    SocialAuthenticationCompleteView,
)

app_name = "authentication"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "verify-email/<str:user_id>/<str:verification_token>",
        EmailVerificationView.as_view(),
        name="verify-email",
    ),
    path(
        f"social/begin/<str:backend>{extra}",
        SocialAuthenticationBeginView.as_view(),
        name="social-begin",
    ),
    path(
        "social/complete/<str:backend>/",
        SocialAuthenticationCompleteView.as_view(),
        name="social-complete",
    ),
]

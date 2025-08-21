from django.urls import include, path

urlpatterns = [
    path("users/", include("api.v1.users")),
    path("authentication/", include("api.v1.authentication")),
    path("business-verification/", include("api.v1.business_verification")),
]

from django.urls import include, path

urlpatterns = [
    path("authentication/", include("api.v1.authentication")),
    path("users/", include("api.v1.users")),
    path("business/", include("api.v1.business")),
    path("location/", include("api.v1.location")),
]

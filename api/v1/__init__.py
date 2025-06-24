from django.urls import include, path

urlpatterns = [
    path("authentication/", include("api.v1.authentication")),
]

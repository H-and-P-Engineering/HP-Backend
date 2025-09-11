from django.urls import path

from app.presentation.views.location import (
    find_nearby_services,
)

app_name = "location"

urlpatterns = [
    path(
        "nearby-services/",
        find_nearby_services,
        name="nearby-services",
    ),
]

from django.urls import path

from app.presentation.views.users import (
    update_user_type,
    update_social_registration_data,
)

app_name = "users"

urlpatterns = [
    path("update-user-type/", update_user_type, name="update-user-type"),
    path(
        "update-social-data/",
        update_social_registration_data,
        name="update-social-data",
    ),
]

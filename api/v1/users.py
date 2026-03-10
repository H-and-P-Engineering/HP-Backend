from django.urls import path, URLPattern

from users.views import (
    update_user_data,
)

app_name = "users"

urlpatterns: list[URLPattern] = [
    path("update/", update_user_data, name="update-data"),
]

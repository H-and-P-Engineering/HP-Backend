from django.urls import path

from app.presentation.views.users import update_user_type

app_name = "users"

urlpatterns = [
    path("update-user-type/", update_user_type, name="update-user-type"),
]

from django.urls import path

from location import views

app_name = "location"

urlpatterns = [
    path("nearby-services/", views.find_nearby_services, name="find-nearby-services"),
    path("distance/", views.calculate_distance, name="calculate-distance"),
]

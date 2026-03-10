from typing import Any

from mapradar import LocationIntelligence
from rest_framework import serializers

from .models import DistanceResult, ServiceType


class NearbyServiceRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=False, min_value=-180, max_value=180)
    address = serializers.CharField(required=False, max_length=500)

    service_types = serializers.ListField(
        child=serializers.ChoiceField(choices=ServiceType.choices()),
        required=False,
        allow_empty=False,
        max_length=11,
    )
    radius_km = serializers.FloatField(
        required=False, default=5.0, min_value=0.1, max_value=50.0
    )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        address = data.get("address")

        if not (latitude and longitude) and not address:
            raise serializers.ValidationError(
                "Either coordinates (latitude and longitude) or address must be provided."
            )

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        if not data.get("service_types"):
            data["service_types"] = [
                ServiceType.BUS_STOP,
                ServiceType.MARKET,
                ServiceType.SCHOOL,
                ServiceType.MALL,
                ServiceType.FUEL_STATION,
                ServiceType.TRAIN_STATION,
                ServiceType.TAXI_STAND,
                ServiceType.LANDMARK,
            ]

        return data


class NearbyServiceResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    service_type = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    distance_km = serializers.FloatField()
    address = serializers.CharField(allow_null=True)
    rating = serializers.FloatField(allow_null=True)
    place_id = serializers.CharField(allow_null=True)


class LocationResponseSerializer(serializers.Serializer):
    address = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    city = serializers.CharField(allow_null=True)
    state = serializers.CharField(allow_null=True)
    country = serializers.CharField()


class LocationIntelligenceResponseSerializer(serializers.Serializer):
    location = LocationResponseSerializer()
    nearby_services = NearbyServiceResponseSerializer(many=True)
    total_services_found = serializers.IntegerField()

    def to_representation(self, instance: LocationIntelligence) -> dict[str, Any]:
        location_data = {
            "address": instance.location.address,
            "latitude": instance.location.latitude,
            "longitude": instance.location.longitude,
            "city": instance.location.city,
            "state": instance.location.state,
            "country": instance.location.country,
        }

        services_data = []
        for service in instance.nearby_services:
            service_data = {
                "name": service.name,
                "service_type": str(service.service_type),
                "latitude": service.latitude,
                "longitude": service.longitude,
                "distance_km": service.distance_km,
                "address": service.address,
                "rating": service.rating,
                "place_id": service.place_id,
            }
            services_data.append(service_data)

        services_by_type: dict[str, list[dict[str, Any]]] = {}
        for service in services_data:
            service_type = service["service_type"]
            if service_type not in services_by_type:
                services_by_type[service_type] = []
            services_by_type[service_type].append(service)

        return {
            "location": location_data,
            "nearby_services": services_data,
            "services_by_type": services_by_type,
            "total_services_found": instance.total_services_found,
            "summary": {
                "total_services": instance.total_services_found,
                "service_types_found": len(services_by_type),
                "has_transportation": any(
                    s["service_type"] in ["BusStop", "TrainStation", "TaxiStand"]
                    for s in services_data
                ),
                "has_shopping": any(
                    s["service_type"] in ["Market", "Mall"] for s in services_data
                ),
                "has_education": any(
                    s["service_type"] == "School" for s in services_data
                ),
                "has_healthcare": any(
                    s["service_type"] == "Hospital" for s in services_data
                ),
            },
        }


class DistanceRequestSerializer(serializers.Serializer):
    origin_latitude = serializers.FloatField(
        required=False, min_value=-90, max_value=90
    )
    origin_longitude = serializers.FloatField(
        required=False, min_value=-180, max_value=180
    )
    origin_address = serializers.CharField(required=False, max_length=500)

    destination_latitude = serializers.FloatField(
        required=False, min_value=-90, max_value=90
    )
    destination_longitude = serializers.FloatField(
        required=False, min_value=-180, max_value=180
    )
    destination_address = serializers.CharField(required=False, max_length=500)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        origin_latitude = data.get("origin_latitude")
        origin_longitude = data.get("origin_longitude")
        origin_address = data.get("origin_address")

        destination_latitude = data.get("destination_latitude")
        destination_longitude = data.get("destination_longitude")
        destination_address = data.get("destination_address")

        has_origin_coords = origin_latitude is not None and origin_longitude is not None
        if not has_origin_coords and not origin_address:
            raise serializers.ValidationError(
                "Either origin coordinates or origin_address must be provided."
            )

        if (origin_latitude is None) != (origin_longitude is None):
            raise serializers.ValidationError(
                "Both origin_latitude and origin_longitude must be provided together."
            )

        has_dest_coords = (
            destination_latitude is not None and destination_longitude is not None
        )
        if not has_dest_coords and not destination_address:
            raise serializers.ValidationError(
                "Either destination coordinates or destination_address must be provided."
            )

        if (destination_latitude is None) != (destination_longitude is None):
            raise serializers.ValidationError(
                "Both destination_latitude and destination_longitude must be provided together."
            )

        return data


class DistanceResponseSerializer(serializers.Serializer):
    origin_address = serializers.CharField()
    origin_latitude = serializers.FloatField()
    origin_longitude = serializers.FloatField()
    destination_address = serializers.CharField()
    destination_latitude = serializers.FloatField()
    destination_longitude = serializers.FloatField()
    distance_km = serializers.FloatField()
    distance_text = serializers.CharField()
    duration_minutes = serializers.FloatField(allow_null=True)
    duration_text = serializers.CharField(allow_null=True)

    def to_representation(self, instance: DistanceResult) -> dict[str, Any]:
        return {
            "origin": {
                "address": instance.origin_address,
                "latitude": instance.origin_latitude,
                "longitude": instance.origin_longitude,
            },
            "destination": {
                "address": instance.destination_address,
                "latitude": instance.destination_latitude,
                "longitude": instance.destination_longitude,
            },
            "distance_km": instance.distance_km,
            "distance_text": instance.distance_text,
            "duration_minutes": instance.duration_minutes,
            "duration_text": instance.duration_text,
        }

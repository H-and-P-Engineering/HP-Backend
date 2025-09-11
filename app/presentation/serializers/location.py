from typing import Any, Dict

from rest_framework import serializers

from app.domain.location.entities import LocationIntelligence
from app.domain.location.enums import ServiceType


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

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
    phone_number = serializers.CharField(allow_null=True)
    rating = serializers.FloatField(allow_null=True)
    website = serializers.URLField(allow_null=True)
    business_hours = serializers.CharField(allow_null=True)
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
    road_connectivity_score = serializers.FloatField(allow_null=True)
    electricity_availability_score = serializers.FloatField(allow_null=True)
    total_services_found = serializers.IntegerField()
    query_timestamp = serializers.DateTimeField(allow_null=True)

    def to_representation(self, instance: LocationIntelligence) -> Dict[str, Any]:
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
                "service_type": service.service_type,
                "latitude": service.latitude,
                "longitude": service.longitude,
                "distance_km": service.distance_km,
                "address": service.address,
                "phone_number": service.phone_number,
                "rating": service.rating,
                "website": service.website,
                "business_hours": service.business_hours,
                "place_id": service.place_id,
            }
            services_data.append(service_data)

        services_by_type = {}
        for service in services_data:
            service_type = service["service_type"]
            if service_type not in services_by_type:
                services_by_type[service_type] = []
            services_by_type[service_type].append(service)

        return {
            "location": location_data,
            "nearby_services": services_data,
            "services_by_type": services_by_type,
            "road_connectivity_score": instance.road_connectivity_score,
            "electricity_availability_score": instance.electricity_availability_score,
            "total_services_found": instance.total_services_found,
            "summary": {
                "total_services": instance.total_services_found,
                "service_types_found": len(services_by_type),
                "has_transportation": any(
                    s["service_type"]
                    in [
                        ServiceType.BUS_STOP,
                        ServiceType.TRAIN_STATION,
                        ServiceType.TAXI_STAND,
                    ]
                    for s in services_data
                ),
                "has_shopping": any(
                    s["service_type"] in [ServiceType.MARKET, ServiceType.MALL]
                    for s in services_data
                ),
                "has_education": any(
                    s["service_type"] == ServiceType.SCHOOL for s in services_data
                ),
                "has_healthcare": any(
                    s["service_type"] == ServiceType.HOSPITAL for s in services_data
                ),
            },
        }

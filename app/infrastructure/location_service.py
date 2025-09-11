import math
from typing import List, Optional

import requests
from django.conf import settings
from loguru import logger

from app.application.location.ports import IGeocodingService, IPlacesService
from app.core.exceptions import BaseAPIException
from app.domain.location.entities import Location, NearbyService
from app.domain.location.enums import ServiceType


class GoogleGeocodingService(IGeocodingService):
    def __init__(self) -> None:
        self.api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        self.base_url = getattr(
            settings,
            "GOOGLE_MAPS_GEOCODE_URL",
            "https://maps.googleapis.com/maps/api/geocode/json",
        )

    def geocode_address(self, address: str) -> Optional[Location]:
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            raise BaseAPIException(
                "Unable to use location services. Please try again later."
            )

        try:
            params = {
                "address": address,
                "key": self.api_key,
                "region": "ng",
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                geometry = result["geometry"]["location"]

                components = result.get("address_components", [])
                city = state = None

                for component in components:
                    types = component.get("types", [])
                    if "locality" in types:
                        city = component["long_name"]
                    elif "administrative_area_level_1" in types:
                        state = component["long_name"]

                return Location(
                    address=result["formatted_address"],
                    latitude=geometry["lat"],
                    longitude=geometry["lng"],
                    city=city,
                    state=state,
                    country="NG",
                )

            logger.warning(f"Geocoding failed for address: {address}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None

        try:
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
                "region": "ng",
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data["status"] == "OK" and data["results"]:
                return data["results"][0]["formatted_address"]

            return None

        except Exception as e:
            logger.error(f"Error during reverse geocoding: {e}")
            return None


class GooglePlacesService(IPlacesService):
    def __init__(self) -> None:
        self.api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        self.base_url = getattr(
            settings,
            "GOOGLE_MAPS_SEARCH_URL",
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
        )

    def find_nearby_services(
        self,
        latitude: float,
        longitude: float,
        service_types: List[ServiceType],
        radius_km: float = 5.0,
        max_results_per_type: int = 5,
    ) -> List[NearbyService]:
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return []

        all_services = []
        radius_meters = min(radius_km * 1000, 50000)

        for service_type in service_types:
            try:
                services = self._search_places_by_type(
                    latitude,
                    longitude,
                    service_type,
                    radius_meters,
                    max_results_per_type,
                )
                all_services.extend(services)
            except Exception as e:
                logger.error(f"Error searching for {service_type}: {e}")
                continue

        all_services.sort(key=lambda x: x.distance_km)
        return all_services

    def _search_places_by_type(
        self,
        latitude: float,
        longitude: float,
        service_type: ServiceType,
        radius_meters: int,
        max_results: int,
    ) -> List[NearbyService]:
        try:
            google_type = ServiceType.get_google_places_type(service_type)

            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius_meters,
                "type": google_type,
                "key": self.api_key,
            }

            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data["status"] != "OK":
                logger.warning(f"Places API error: {data.get('status')}")
                return []

            services = []
            for place in data.get("results", [])[:max_results]:
                try:
                    service = self._convert_place_to_service(
                        place, service_type, latitude, longitude
                    )
                    if service:
                        services.append(service)
                except Exception as e:
                    logger.error(f"Error converting place to service: {e}")
                    continue

            return services

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during places search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during places search: {e}")
            return []

    def _convert_place_to_service(
        self,
        place: dict,
        service_type: ServiceType,
        origin_lat: float,
        origin_lng: float,
    ) -> Optional[NearbyService]:
        try:
            location = place.get("geometry", {}).get("location", {})
            place_lat = location.get("lat")
            place_lng = location.get("lng")

            if not place_lat or not place_lng:
                return None

            distance_km = self._calculate_distance(
                origin_lat, origin_lng, place_lat, place_lng
            )

            return NearbyService(
                name=place.get("name", "Unknown"),
                service_type=service_type,
                latitude=place_lat,
                longitude=place_lng,
                distance_km=round(distance_km, 3),
                address=place.get("vicinity"),
                rating=place.get("rating"),
                place_id=place.get("place_id"),
            )

        except Exception as e:
            logger.error(f"Error converting place data: {e}")
            return None

    def _calculate_distance(
        self, lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

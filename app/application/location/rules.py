import hashlib
from typing import Any, Callable, List

from app.core.exceptions import BusinessRuleException
from app.domain.location.entities import Location, LocationIntelligence
from app.domain.location.enums import ServiceType

from .ports import IGeocodingService, IPlacesService


class ProcessLocationQueryRule:
    def __init__(
        self,
        cache_service: Callable[[Any], str],
        geocoding_service: IGeocodingService,
        places_service: IPlacesService,
        event_publisher: Callable[[Any], Any],
    ) -> None:
        self.cache_service = cache_service
        self.geocoding_service = geocoding_service
        self.places_service = places_service
        self.event_publisher = event_publisher

    def __call__(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        service_types: List[ServiceType] | None = None,
        radius_km: float = 5.0,
        event: Callable[[Any], Any] | None = None,
    ) -> LocationIntelligence:
        params_string = f"{latitude}{longitude}{address}{service_types}{radius_km}"
        cache_key = hashlib.md5(params_string.encode("utf-8")).hexdigest()
        cached_query = self.cache_service.get(cache_key)

        if cached_query and cached_query.nearby_services:
            return cached_query

        if not latitude or not longitude:
            if not address:
                raise BusinessRuleException(
                    "Either coordinates (latitude/longitude) or address must be provided"
                )

            location = self.geocoding_service.geocode_address(address)
            if not location:
                raise BusinessRuleException(f"Could not geocode address: {address}")
            latitude, longitude = location.latitude, location.longitude
        else:
            reverse_address = self.geocoding_service.reverse_geocode(
                latitude, longitude
            )
            location = Location(
                address=reverse_address or f"{latitude}, {longitude}",
                latitude=latitude,
                longitude=longitude,
            )

        if radius_km <= 0 or radius_km > 50:
            raise BusinessRuleException("Radius must be between 0.1 and 50 kilometers")

        if not service_types:
            service_types = [
                ServiceType.BUS_STOP,
                ServiceType.MARKET,
                ServiceType.SCHOOL,
                ServiceType.MALL,
                ServiceType.FUEL_STATION,
                ServiceType.TRAIN_STATION,
                ServiceType.TAXI_STAND,
                ServiceType.LANDMARK,
            ]

        nearby_services = self.places_service.find_nearby_services(
            latitude=latitude,
            longitude=longitude,
            service_types=service_types,
            radius_km=radius_km,
        )

        location_intelligence = LocationIntelligence(
            location=location,
            nearby_services=nearby_services,
            road_connectivity_score=self._calculate_road_connectivity_score(
                nearby_services
            ),
            electricity_availability_score=self._calculate_electricity_score(
                nearby_services
            ),
            total_services_found=len(nearby_services),
        )

        self.cache_service.set(cache_key, location_intelligence)

        if event:
            self.event_publisher.publish(event(cache_key, location_intelligence))

        return location_intelligence

    def _calculate_road_connectivity_score(self, services: List) -> float:
        bus_stops = [s for s in services if s.service_type == ServiceType.BUS_STOP]
        fuel_stations = [
            s for s in services if s.service_type == ServiceType.FUEL_STATION
        ]
        train_stations = [
            s for s in services if s.service_type == ServiceType.TRAIN_STATION
        ]
        taxi_stands = [s for s in services if s.service_type == ServiceType.TAXI_STAND]
        markets = [s for s in services if s.service_type == ServiceType.MARKET]
        schools = [s for s in services if s.service_type == ServiceType.SCHOOL]
        banks = [s for s in services if s.service_type == ServiceType.BANK]
        hospitals = [s for s in services if s.service_type == ServiceType.HOSPITAL]

        score = (
            len(bus_stops) * 20
            + len(fuel_stations) * 10
            + len(train_stations) * 30
            + len(taxi_stands) * 15
            + len(markets) * 5
            + len(schools) * 5
            + len(banks) * 5
            + len(hospitals) * 5
        )
        return round(min(score, 100), 2)

    def _calculate_electricity_score(self, services: List) -> float:
        banks = [s for s in services if s.service_type == ServiceType.BANK]
        malls = [s for s in services if s.service_type == ServiceType.MALL]
        hospitals = [s for s in services if s.service_type == ServiceType.HOSPITAL]

        score = min(len(banks) * 15 + len(malls) * 25 + len(hospitals) * 20, 100)
        return round(score, 2)

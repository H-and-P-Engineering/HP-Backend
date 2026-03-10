import hashlib
import json

from django.conf import settings
from loguru import logger
from mapradar import (
    GeoLocation,
    LocationIntelligence,
    MapradarClient,
    SearchQuery,
)

from core.exceptions import BadRequestError
from core.services import BaseCacheService
from core.container import container
from .models import DistanceResult, ServiceType


from .utils import TravelCalculator


class LocationCacheService(BaseCacheService):
    def __init__(self) -> None:
        super().__init__(prefix="location", timeout=settings.CACHE_LOCATION_TIMEOUT)

    def _make_key(self, *args: str) -> str:
        key_data = ":".join(str(a) for a in args)
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    async def get_geocode(self, address: str) -> GeoLocation | None:
        key = f"geocode:{self._make_key(address.lower().strip())}"
        cached = self.get(key)
        if cached:
            if isinstance(cached, str):
                data = json.loads(cached)
            else:
                data = cached
            return GeoLocation(
                address=data["address"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                city=data.get("city"),
                state=data.get("state"),
                country=data.get("country", "NG"),
            )
        return None

    async def set_geocode(self, address: str, location: GeoLocation) -> None:
        key = f"geocode:{self._make_key(address.lower().strip())}"
        data = {
            "address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "city": location.city,
            "state": location.state,
            "country": location.country,
        }
        self.set(key, data)

    async def get_reverse_geocode(
        self, latitude: float, longitude: float
    ) -> str | None:
        key = f"reverse:{self._make_key(f'{latitude:.6f}', f'{longitude:.6f}')}"
        return self.get(key)

    async def set_reverse_geocode(
        self, latitude: float, longitude: float, address: str
    ) -> None:
        key = f"reverse:{self._make_key(f'{latitude:.6f}', f'{longitude:.6f}')}"
        self.set(key, address)


class GeocodingService:
    def __init__(
        self,
        client: MapradarClient | None = None,
        cache: LocationCacheService | None = None,
    ) -> None:
        if client:
            self.client = client
        else:
            api_key = getattr(settings, "MAPRADAR_API_KEY", "")
            if api_key:
                self.client = MapradarClient(api_key=api_key)
            else:
                self.client = None
        self.cache = cache or LocationCacheService()

    async def geocode_address(self, address: str) -> GeoLocation | None:
        client = self.client
        if not client:
            temp_client = container.get(
                "mapradar_client",
                MapradarClient,
                api_key=getattr(settings, "MAPRADAR_API_KEY", ""),
            )
            client = temp_client

        if not client:
            logger.warning("Mapradar API key not configured")
            raise BadRequestError(
                "Location services not configured. Please try again later."
            )

        cached = await self.cache.get_geocode(address)
        if cached:
            logger.debug("Cache hit for geocode", address=address)
            return cached

        try:
            result = await client.geocode(address)
            if result:
                await self.cache.set_geocode(address, result)
                return result
            return None
        except Exception as e:
            logger.error("Error during geocoding", error=str(e))
            return None

    async def reverse_geocode(self, latitude: float, longitude: float) -> str | None:
        client = self.client
        if not client:
            temp_client = container.get(
                "mapradar_client",
                MapradarClient,
                api_key=getattr(settings, "MAPRADAR_API_KEY", ""),
            )
            client = temp_client

        if not client:
            logger.warning("Mapradar API key not configured")
            return None

        cached = await self.cache.get_reverse_geocode(latitude, longitude)
        if cached:
            logger.debug(
                "Cache hit for reverse geocode",
                latitude=latitude,
                longitude=longitude,
            )
            return cached

        try:
            result = await client.reverse_geocode(latitude, longitude)
            if result:
                await self.cache.set_reverse_geocode(
                    latitude, longitude, result.address
                )
                return result.address
            return None
        except Exception as e:
            logger.error("Error during reverse geocoding", error=str(e))
            return None


class TravelService:
    def __init__(
        self,
        geocoding_service: GeocodingService | None = None,
        calculator: TravelCalculator | None = None,
    ) -> None:
        self.geocoding_service = geocoding_service or container.geocoding_service()
        self.calculator = calculator or TravelCalculator()

    async def calculate_distance(
        self,
        origin_latitude: float | None = None,
        origin_longitude: float | None = None,
        origin_address: str | None = None,
        destination_latitude: float | None = None,
        destination_longitude: float | None = None,
        destination_address: str | None = None,
    ) -> DistanceResult:
        # Resolve origin
        if origin_latitude is not None and origin_longitude is not None:
            origin_addr = await self.geocoding_service.reverse_geocode(
                origin_latitude, origin_longitude
            )
            origin_address = origin_addr or ""
        elif origin_address:
            origin = await self.geocoding_service.geocode_address(origin_address)
            if not origin:
                raise BadRequestError("Could not geocode the origin address.")
            origin_latitude, origin_longitude, origin_address = (
                origin.latitude,
                origin.longitude,
                origin.address,
            )
        else:
            raise BadRequestError("Origin coordinates or address required.")

        # Resolve destination
        if destination_latitude is not None and destination_longitude is not None:
            dest_addr = await self.geocoding_service.reverse_geocode(
                destination_latitude, destination_longitude
            )
            destination_address = dest_addr or ""
        elif destination_address:
            destination = await self.geocoding_service.geocode_address(
                destination_address
            )
            if not destination:
                raise BadRequestError("Could not geocode the destination address.")
            destination_latitude, destination_longitude, destination_address = (
                destination.latitude,
                destination.longitude,
                destination.address,
            )
        else:
            raise BadRequestError("Destination coordinates or address required.")

        distance_km = self.calculator.calculate_haversine_distance(
            origin_latitude,
            origin_longitude,
            destination_latitude,
            destination_longitude,
        )
        duration_minutes, duration_text = self.calculator.estimate_duration(distance_km)

        return DistanceResult(
            origin_address=origin_address,
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            destination_address=destination_address,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
            distance_km=distance_km,
            distance_text=self.calculator.format_distance(distance_km),
            duration_minutes=round(duration_minutes, 1),
            duration_text=duration_text,
        )


DEFAULT_INTELLIGENCE_SERVICES = [
    ServiceType.BUS_STOP,
    ServiceType.MARKET,
    ServiceType.SCHOOL,
    ServiceType.MALL,
    ServiceType.FUEL_STATION,
    ServiceType.TRAIN_STATION,
    ServiceType.TAXI_STAND,
    ServiceType.LANDMARK,
]


class LocationIntelligenceService:
    def __init__(
        self,
        geocoding_service: GeocodingService | None = None,
        default_service_types: list[ServiceType] | None = None,
    ) -> None:
        self.geocoding_service = geocoding_service or container.geocoding_service()
        self.default_service_types = (
            default_service_types or DEFAULT_INTELLIGENCE_SERVICES
        )

    async def get_location_intelligence(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        service_types: list[ServiceType] | None = None,
        radius_km: float = 5.0,
    ) -> LocationIntelligence:
        client = self.geocoding_service.client
        if not client:
            temp_client = container.get(
                "mapradar_client",
                MapradarClient,
                api_key=getattr(settings, "MAPRADAR_API_KEY", ""),
            )
            client = temp_client

        if not client:
            raise BadRequestError("Location services not configured.")

        service_types = service_types or self.default_service_types

        if not latitude or not longitude:
            if not address:
                raise BadRequestError("Either coordinates or address must be provided.")
            query = SearchQuery.from_address(address)
        else:
            query = SearchQuery.from_coordinates(latitude, longitude)

        mapradar_service_types = [ServiceType.to_mapradar(st) for st in service_types]

        try:
            intel = await client.fetch_intelligence(
                query=query,
                service_types=mapradar_service_types,
                radius_km=radius_km,
                max_results_per_type=5,
            )
            return intel

        except Exception as e:
            logger.error("Error getting location intelligence", error=str(e))
            raise BadRequestError(f"Location service error: {e}")

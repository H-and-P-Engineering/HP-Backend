from typing import List, Protocol

from app.domain.location.entities import Location, NearbyService
from app.domain.location.enums import ServiceType


class IGeocodingService(Protocol):
    def geocode_address(self, address: str) -> Location | None: ...

    def reverse_geocode(self, latitude: float, longitude: float) -> str | None: ...


class IPlacesService(Protocol):
    def find_nearby_services(
        self,
        latitude: float,
        longitude: float,
        service_types: List[ServiceType],
        radius_km: float = 5.0,
        max_results_per_type: int = 5,
    ) -> List[NearbyService]: ...

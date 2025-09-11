from dataclasses import dataclass
from datetime import datetime
from typing import List, Type
from uuid import UUID

from .enums import ServiceType


@dataclass
class Location:
    address: str
    latitude: float
    longitude: float
    city: str | None = None
    state: str | None = None
    country: str = "NG"
    id: int | None = None
    uuid: Type[UUID] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class NearbyService:
    name: str
    service_type: ServiceType
    latitude: float
    longitude: float
    distance_km: float
    address: str | None = None
    phone_number: str | None = None
    rating: float | None = None
    website: str | None = None
    business_hours: str | None = None
    place_id: str | None = None


@dataclass
class LocationIntelligence:
    location: Location
    nearby_services: List[NearbyService]
    road_connectivity_score: float | None = None
    electricity_availability_score: float | None = None
    total_services_found: int = 0
    query_timestamp: datetime | None = None

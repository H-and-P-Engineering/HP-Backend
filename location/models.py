from dataclasses import dataclass
from enum import StrEnum

from mapradar import ServiceType as MapradarServiceType


class ServiceType(StrEnum):
    BUS_STOP = "BUS_STOP"
    MARKET = "MARKET"
    SCHOOL = "SCHOOL"
    MALL = "MALL"
    HOSPITAL = "HOSPITAL"
    BANK = "BANK"
    RESTAURANT = "RESTAURANT"
    FUEL_STATION = "FUEL_STATION"
    TRAIN_STATION = "TRAIN_STATION"
    TAXI_STAND = "TAXI_STAND"
    LANDMARK = "LANDMARK"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def to_mapradar(cls, service_type: "ServiceType") -> MapradarServiceType:
        mapping = {
            cls.BUS_STOP: MapradarServiceType.BusStop,
            cls.MARKET: MapradarServiceType.Market,
            cls.SCHOOL: MapradarServiceType.School,
            cls.MALL: MapradarServiceType.Mall,
            cls.HOSPITAL: MapradarServiceType.Hospital,
            cls.BANK: MapradarServiceType.Bank,
            cls.RESTAURANT: MapradarServiceType.Restaurant,
            cls.FUEL_STATION: MapradarServiceType.FuelStation,
            cls.TRAIN_STATION: MapradarServiceType.TrainStation,
            cls.TAXI_STAND: MapradarServiceType.TaxiStand,
            cls.LANDMARK: MapradarServiceType.Landmark,
        }
        return mapping.get(service_type, MapradarServiceType.Bank)


@dataclass
class DistanceResult:
    origin_address: str
    origin_latitude: float
    origin_longitude: float
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    distance_km: float
    distance_text: str
    duration_minutes: float | None = None
    duration_text: str | None = None

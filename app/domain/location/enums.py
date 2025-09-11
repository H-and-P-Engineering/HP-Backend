from enum import StrEnum
from typing import List, Tuple


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
    def choices(cls) -> List[Tuple[str, str]]:
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls) -> List[str]:
        return [member.value for member in cls]

    @classmethod
    def get_google_places_type(cls, service_type: "ServiceType") -> str:
        mapping = {
            cls.BUS_STOP: "bus_station",
            cls.MARKET: "supermarket",
            cls.SCHOOL: "school",
            cls.MALL: "shopping_mall",
            cls.HOSPITAL: "hospital",
            cls.BANK: "bank",
            cls.RESTAURANT: "restaurant",
            cls.FUEL_STATION: "gas_station",
            cls.TRAIN_STATION: "train_station",
            cls.TAXI_STAND: "taxi_stand",
            cls.LANDMARK: "tourist_attraction",
        }
        return mapping.get(service_type, "establishment")

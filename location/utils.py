import math


class TravelCalculator:
    EARTH_RADIUS_KM = 6371

    @staticmethod
    def calculate_haversine_distance(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        latitude_1_radians = math.radians(latitude_1)
        latitude_2_radians = math.radians(latitude_2)
        delta_latitude = math.radians(latitude_2_radians - latitude_1_radians)
        delta_longitude = math.radians(longitude_2 - longitude_1)

        a = (
            math.sin(delta_latitude / 2) ** 2
            + math.cos(latitude_1_radians)
            * math.cos(latitude_2_radians)
            * math.sin(delta_longitude / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return round(TravelCalculator.EARTH_RADIUS_KM * c, 2)

    @staticmethod
    def format_distance(distance_km: float) -> str:
        if distance_km < 1:
            return f"{int(distance_km * 1000)} m"
        return f"{distance_km:.1f} km"

    @staticmethod
    def estimate_duration(
        distance_km: float, avg_speed_kmh: int = 30
    ) -> tuple[float, str]:
        duration_hours = distance_km / avg_speed_kmh
        duration_minutes = duration_hours * 60

        if duration_minutes < 60:
            return duration_minutes, f"{int(duration_minutes)} mins"
        else:
            hours = int(duration_minutes // 60)
            mins = int(duration_minutes % 60)
            return duration_minutes, f"{hours} hr {mins} mins"

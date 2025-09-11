from app.core.events import DomainEvent
from app.domain.location.entities import LocationIntelligence


class ProcessLocationEvent(DomainEvent):
    def __init__(self, cache_key: str, location_intelligence: LocationIntelligence):
        self.cache_key = cache_key
        self.location_intelligence = location_intelligence

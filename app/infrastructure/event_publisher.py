import pickle

from app.core.celery import publish_event_to_bus
from app.core.events import DomainEvent


class EventPublisher:
    def publish(self, event: DomainEvent) -> None:
        event_data = pickle.dumps(event)
        publish_event_to_bus.delay(event_data)

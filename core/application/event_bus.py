from typing import Callable, Dict, List, Type

from core.domain.events import DomainEvent


class EventBus:
    _handlers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}

    @classmethod
    def subscribe(
        cls, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        exceptions = []
        for handler in cls._handlers.get(type(event), []):
            try:
                handler(event)
            except Exception as e:
                exceptions.append(e)

        if exceptions:
            raise exceptions[0]

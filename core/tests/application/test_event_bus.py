from unittest.mock import Mock

import pytest

from core.application.event_bus import EventBus
from core.domain.events import DomainEvent


class TestEvent(DomainEvent):
    def __init__(self, data):
        self.data = data


class AnotherTestEvent(DomainEvent):
    def __init__(self, value):
        self.value = value


class TestEventBus:
    def setup_method(self):
        EventBus._handlers.clear()

    def teardown_method(self):
        EventBus._handlers.clear()

    def test_subscribe_single_handler(self):
        handler = Mock()

        EventBus.subscribe(TestEvent, handler)

        assert TestEvent in EventBus._handlers
        assert handler in EventBus._handlers[TestEvent]

    def test_subscribe_multiple_handlers_same_event(self):
        handler1 = Mock()
        handler2 = Mock()

        EventBus.subscribe(TestEvent, handler1)
        EventBus.subscribe(TestEvent, handler2)

        assert len(EventBus._handlers[TestEvent]) == 2
        assert handler1 in EventBus._handlers[TestEvent]
        assert handler2 in EventBus._handlers[TestEvent]

    def test_subscribe_different_events(self):
        handler1 = Mock()
        handler2 = Mock()

        EventBus.subscribe(TestEvent, handler1)
        EventBus.subscribe(AnotherTestEvent, handler2)

        assert TestEvent in EventBus._handlers
        assert AnotherTestEvent in EventBus._handlers
        assert handler1 in EventBus._handlers[TestEvent]
        assert handler2 in EventBus._handlers[AnotherTestEvent]

    def test_publish_calls_handlers(self):
        handler = Mock()
        event = TestEvent("test_data")

        EventBus.subscribe(TestEvent, handler)
        EventBus.publish(event)

        handler.assert_called_once_with(event)

    def test_publish_calls_multiple_handlers(self):
        handler1 = Mock()
        handler2 = Mock()
        event = TestEvent("test_data")

        EventBus.subscribe(TestEvent, handler1)
        EventBus.subscribe(TestEvent, handler2)
        EventBus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_publish_no_handlers_registered(self):
        event = TestEvent("test_data")

        # Should not raise exception
        EventBus.publish(event)

    def test_publish_only_calls_handlers_for_correct_event_type(self):
        handler1 = Mock()
        handler2 = Mock()
        event = TestEvent("test_data")

        EventBus.subscribe(TestEvent, handler1)
        EventBus.subscribe(AnotherTestEvent, handler2)
        EventBus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_not_called()

    def test_handler_exception_does_not_stop_other_handlers(self):
        handler1 = Mock(side_effect=Exception("Handler 1 failed"))
        handler2 = Mock()
        event = TestEvent("test_data")

        EventBus.subscribe(TestEvent, handler1)
        EventBus.subscribe(TestEvent, handler2)

        with pytest.raises(Exception, match="Handler 1 failed"):
            EventBus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

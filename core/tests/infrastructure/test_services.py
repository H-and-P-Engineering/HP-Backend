import pickle
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from core.domain.events import DomainEvent
from core.infrastructure.exceptions import BaseAPIException
from core.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoEventPublisherAdapter,
    DjangoVerificationServiceAdapter,
    _publish_event_to_bus,
)


class TestDjangoCacheServiceAdapter:
    def setup_method(self):
        self.cache_service = DjangoCacheServiceAdapter()

    @patch("core.infrastructure.services.cache")
    def test_get_returns_cached_value(self, mock_cache):
        mock_cache.get.return_value = "cached_value"

        result = self.cache_service.get("test_key")

        mock_cache.get.assert_called_once_with("test_key", None)
        assert result == "cached_value"

    @patch("core.infrastructure.services.cache")
    def test_get_returns_none_when_key_not_found(self, mock_cache):
        mock_cache.get.return_value = None

        result = self.cache_service.get("nonexistent_key")

        mock_cache.get.assert_called_once_with("nonexistent_key", None)
        assert result is None

    @patch("core.infrastructure.services.cache")
    @patch("django.conf.settings.DJANGO_CACHE_TIMEOUT", 300)
    def test_set_uses_default_timeout(self, mock_cache):
        self.cache_service.set("test_key", "test_value")

        mock_cache.set.assert_called_once_with("test_key", "test_value", 300)

    @patch("core.infrastructure.services.cache")
    def test_set_uses_custom_timeout(self, mock_cache):
        self.cache_service.set("test_key", "test_value", timeout=600)

        mock_cache.set.assert_called_once_with("test_key", "test_value", 600)

    @patch("core.infrastructure.services.cache")
    def test_delete_calls_cache_delete(self, mock_cache):
        self.cache_service.delete("test_key")

        mock_cache.delete.assert_called_once_with("test_key")

    @patch("core.infrastructure.services.cache")
    def test_delete_handles_exception_silently(self, mock_cache):
        mock_cache.delete.side_effect = Exception("Cache error")

        # Should not raise exception
        self.cache_service.delete("test_key")

        mock_cache.delete.assert_called_once_with("test_key")


class TestDjangoEmailServiceAdapter:
    def setup_method(self):
        self.email_service = DjangoEmailServiceAdapter()

    @patch.object(DjangoEmailServiceAdapter, "_send_template_email")
    @patch("django.conf.settings.DJANGO_VERIFICATION_TOKEN_EXPIRY", 15)
    def test_send_verification_email_success(self, mock_send_template_email):
        recipient_email = "test@example.com"
        verification_link = "https://example.com/verify/123"

        self.email_service.send_verification_email(recipient_email, verification_link)

        mock_send_template_email.assert_called_once_with(
            subject="Verify your email address",
            template_name="verify_email",
            context={
                "email": recipient_email,
                "expiry_minutes": 15,
                "verification_link": verification_link,
            },
            recipient_list=[recipient_email],
        )

    @patch.object(DjangoEmailServiceAdapter, "_send_template_email")
    def test_send_verification_email_exception(self, mock_send_template_email):
        mock_send_template_email.side_effect = Exception("SMTP Error")

        with pytest.raises(BaseAPIException, match="Failed to send verification email"):
            self.email_service.send_verification_email(
                "test@example.com", "https://example.com/verify"
            )

    @patch.object(DjangoEmailServiceAdapter, "_send_template_email")
    def test_send_business_verification_success_email(self, mock_send_template_email):
        self.email_service.send_business_verification_success_email(
            recipient_email="business@example.com",
            business_name="Test Business",
            registration_number="RC123456",
            provider_reference="REF123",
        )

        mock_send_template_email.assert_called_once()
        call_args = mock_send_template_email.call_args
        assert (
            call_args[1]["subject"]
            == "Business Verification Successful - Test Business"
        )
        assert call_args[1]["template_name"] == "business_verification_success"
        assert "Test Business" in str(call_args[1]["context"])

    @patch("core.infrastructure.services.render_to_string")
    @patch("core.infrastructure.services.strip_tags")
    @patch("core.infrastructure.services.EmailMultiAlternatives")
    @patch("django.conf.settings.DEFAULT_FROM_EMAIL", "noreply@example.com")
    def test_send_template_email_success(
        self, mock_email_class, mock_strip_tags, mock_render
    ):
        mock_render.return_value = "<html>Test content</html>"
        mock_strip_tags.return_value = "Test content"
        mock_email_instance = Mock()
        mock_email_class.return_value = mock_email_instance
        mock_email_instance.send.return_value = 1

        result = self.email_service._send_template_email(
            subject="Test Subject",
            template_name="test_template",
            context={"key": "value"},
            recipient_list=["test@example.com"],
        )

        mock_render.assert_called_once_with("test_template.html", {"key": "value"})
        mock_strip_tags.assert_called_once_with("<html>Test content</html>")
        mock_email_class.assert_called_once_with(
            subject="Test Subject",
            body="Test content",
            from_email="noreply@example.com",
            to=["test@example.com"],
        )
        mock_email_instance.attach_alternative.assert_called_once_with(
            "<html>Test content</html>", "text/html"
        )
        mock_email_instance.send.assert_called_once()
        assert result == 1


class TestDomainEvent(DomainEvent):
    def __init__(self, data):
        self.data = data


class TestDjangoEventPublisherAdapter:
    def setup_method(self):
        self.event_publisher = DjangoEventPublisherAdapter()

    @patch("core.infrastructure.services._publish_event_to_bus.delay")
    def test_publish_calls_celery_task(self, mock_delay):
        event = TestDomainEvent("test_data")

        self.event_publisher.publish(event)

        mock_delay.assert_called_once()
        # Verify the event was pickled
        call_args = mock_delay.call_args[0][0]
        unpickled_event = pickle.loads(call_args)
        assert isinstance(unpickled_event, TestDomainEvent)
        assert unpickled_event.data == "test_data"


class TestPublishEventToBusTask:
    @patch("core.infrastructure.services.EventBus.publish")
    def test_publish_event_to_bus_unpickles_and_publishes(self, mock_event_bus_publish):
        event = TestDomainEvent("test_data")
        event_data = pickle.dumps(event)

        _publish_event_to_bus(event_data)

        mock_event_bus_publish.assert_called_once()
        published_event = mock_event_bus_publish.call_args[0][0]
        assert isinstance(published_event, TestDomainEvent)
        assert published_event.data == "test_data"


class TestDjangoVerificationServiceAdapter:
    def setup_method(self):
        self.verification_service = DjangoVerificationServiceAdapter()

    @patch("core.infrastructure.services.secrets.token_urlsafe")
    def test_generate_token(self, mock_token_urlsafe):
        mock_token_urlsafe.return_value = "generated_token_12345"

        token = self.verification_service.generate_token()

        mock_token_urlsafe.assert_called_once_with(32)
        assert token == "generated_token_12345"

    @patch("core.infrastructure.services.reverse")
    @patch("django.conf.settings.FROM_DOMAIN", "https://example.com")
    def test_generate_email_verification_link_user(self, mock_reverse):
        verification_uuid = uuid4()
        verification_token = "test_token"
        mock_reverse.return_value = "/auth/verify/123/token/"

        link = self.verification_service.generate_email_verification_link(
            verification_uuid, verification_token, is_business=False
        )

        mock_reverse.assert_called_once_with(
            "authentication:verify-email",
            kwargs={
                "user_uuid": verification_uuid,
                "verification_token": verification_token,
            },
        )
        assert link == "https://example.com/auth/verify/123/token/"

    @patch("core.infrastructure.services.reverse")
    @patch("django.conf.settings.FROM_DOMAIN", "https://example.com")
    def test_generate_email_verification_link_business(self, mock_reverse):
        verification_uuid = uuid4()
        verification_token = "test_token"
        mock_reverse.return_value = "/business/verify/123/token/"

        link = self.verification_service.generate_email_verification_link(
            verification_uuid, verification_token, is_business=True
        )

        mock_reverse.assert_called_once_with(
            "business_verification:verify-business-email",
            kwargs={
                "verification_uuid": verification_uuid,
                "verification_token": verification_token,
            },
        )
        assert link == "https://example.com/business/verify/123/token/"

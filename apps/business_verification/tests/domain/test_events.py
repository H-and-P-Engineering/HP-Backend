from apps.business_verification.domain.events import (
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationEmailEvent,
    BusinessVerificationEvent,
    BusinessVerificationFailedEvent,
    BusinessVerificationRequestedEvent,
    BusinessVerificationSuccessfulEvent,
)


class TestBusinessVerificationEvents:
    def test_business_verification_event_base(self):
        event = BusinessVerificationEvent(verification_id=1)
        assert event.verification_id == 1

    def test_business_verification_requested_event(self):
        event = BusinessVerificationRequestedEvent(verification_id=1)
        assert event.verification_id == 1
        assert isinstance(event, BusinessVerificationEvent)

    def test_business_verification_successful_event(self):
        event = BusinessVerificationSuccessfulEvent(
            verification_id=1,
            user_id=2,
            business_name="Test Business",
            business_email="test@business.com",
        )
        assert event.verification_id == 1
        assert event.user_id == 2
        assert event.business_name == "Test Business"
        assert event.business_email == "test@business.com"
        assert isinstance(event, BusinessVerificationEvent)

    def test_business_verification_failed_event(self):
        event = BusinessVerificationFailedEvent(
            verification_id=1,
            user_id=2,
            business_name="Test Business",
            business_email="test@business.com",
            error_reason="Invalid registration number",
        )
        assert event.verification_id == 1
        assert event.user_id == 2
        assert event.business_name == "Test Business"
        assert event.business_email == "test@business.com"
        assert event.error_reason == "Invalid registration number"
        assert isinstance(event, BusinessVerificationEvent)

    def test_business_verification_failed_event_no_error_reason(self):
        event = BusinessVerificationFailedEvent(
            verification_id=1,
            user_id=2,
            business_name="Test Business",
            business_email="test@business.com",
        )
        assert event.error_reason is None

    def test_business_verification_email_event(self):
        event = BusinessVerificationEmailEvent(verification_id=1)
        assert event.verification_id == 1
        assert isinstance(event, BusinessVerificationEvent)

    def test_business_email_verification_successful_event(self):
        event = BusinessEmailVerificationSuccessfulEvent(verification_id=1)
        assert event.verification_id == 1
        assert isinstance(event, BusinessVerificationEvent)

from app.core.events import DomainEvent


class BusinessVerificationEvent(DomainEvent):
    def __init__(self, verification_id: int):
        self.verification_id = verification_id


class BusinessVerificationRequestedEvent(BusinessVerificationEvent):
    pass


class BusinessVerificationStatusEvent(BusinessVerificationEvent):
    def __init__(
        self,
        verification_id: int,
        success: bool,
        user_id: int,
        business_name: str,
        business_email: str,
        error_reason: str | None = None,
    ):
        super().__init__(verification_id)
        self.success = success
        self.user_id = user_id
        self.business_name = business_name
        self.business_email = business_email
        self.error_reason = error_reason


class BusinessEmailVerificationRequestedEvent(BusinessVerificationEvent):
    pass


class BusinessEmailVerificationSuccessfulEvent(BusinessVerificationEvent):
    pass

from core.domain.events import DomainEvent


class BusinessVerificationEvent(DomainEvent):
    def __init__(self, verification_id: int):
        self.verification_id = verification_id


class BusinessVerificationRequestedEvent(BusinessVerificationEvent):
    pass


class BusinessVerificationSuccessfulEvent(BusinessVerificationEvent):
    def __init__(
        self,
        verification_id: int,
        user_id: int,
        business_name: str,
        business_email: str,
    ):
        super().__init__(verification_id)
        self.user_id = user_id
        self.business_name = business_name
        self.business_email = business_email


class BusinessVerificationFailedEvent(BusinessVerificationEvent):
    def __init__(
        self,
        verification_id: int,
        user_id: int,
        business_name: str,
        business_email: str,
        error_reason: str = None,
    ):
        super().__init__(verification_id)
        self.user_id = user_id
        self.business_name = business_name
        self.business_email = business_email
        self.error_reason = error_reason


class BusinessVerificationEmailEvent(BusinessVerificationEvent):
    pass


class BusinessEmailVerificationSuccessfulEvent(BusinessVerificationEvent):
    pass

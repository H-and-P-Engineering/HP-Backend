from dataclasses import dataclass


@dataclass(frozen=True)
class EmailType:
    subject: str
    template_name: str


class EmailTypes:
    USER_VERIFICATION = EmailType(
        subject="Verify your email address", template_name="verify_email"
    )
    BUSINESS_VERIFICATION = EmailType(
        subject="Verify your business email address", template_name="verify_email"
    )
    BUSINESS_VERIFICATION_SUCCESS = EmailType(
        subject="Business Verification Successful",
        template_name="business_verification_success",
    )
    BUSINESS_VERIFICATION_FAILURE = EmailType(
        subject="Business Verification Failed",
        template_name="business_verification_failure",
    )

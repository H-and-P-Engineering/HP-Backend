from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from app.infrastructure.business_verification.events import (
    BusinessEmailVerificationRequestedEvent,
    BusinessEmailVerificationSuccessfulEvent,
    BusinessVerificationRequestedEvent,
)
from app.presentation.factory import (
    get_business_email_verification_request_rule,
    get_business_verification_repository,
    get_create_business_profile_rule,
    get_verify_business_email_rule,
    get_verify_business_rule,
)
from app.presentation.responses import StandardResponse
from app.presentation.serializers.business_verification import (
    BusinessEmailVerificationRequestSerializer,
    BusinessProfileCreationSerializer,
    BusinessProfileResponseSerializer,
    BusinessVerificationInitiationSerializer,
    BusinessVerificationResponseSerializer,
)
from app.presentation.serializers.examples import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)


@extend_schema(
    request=BusinessProfileCreationSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
    },
    description="Create a business profile",
    tags=["Business Verification"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def create_business_profile(request: Request) -> Response:
    serializer = BusinessProfileCreationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    create_business_profile_rule = get_create_business_profile_rule()
    business_profile = create_business_profile_rule(
        user_id=request.user.id,
        business_name=serializer.validated_data["business_name"],
        business_email=serializer.validated_data["business_email"],
        registration_number=serializer.validated_data["registration_number"],
        address=serializer.validated_data.get("address"),
        phone_number=serializer.validated_data.get("phone_number"),
        website=serializer.validated_data.get("website"),
    )

    response_serializer = BusinessProfileResponseSerializer(business_profile)

    return StandardResponse.created(
        data=response_serializer.data, message="Business profile created successfully"
    )


@extend_schema(
    request=BusinessVerificationInitiationSerializer,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
    },
    description="Initiate business verification process",
    tags=["Business Verification"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def verify_business(request: Request) -> Response:
    serializer = BusinessVerificationInitiationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    verify_business_rule = get_verify_business_rule()
    verification = verify_business_rule(
        user_id=request.user.id,
        country_code=serializer.validated_data["country_code"],
        event=BusinessVerificationRequestedEvent,
    )

    response_serializer = BusinessVerificationResponseSerializer(verification)

    return StandardResponse.created(
        data=response_serializer.data,
        message="Business verification initiated successfully",
    )


@extend_schema(
    responses={
        200: BusinessVerificationResponseSerializer,
        404: ErrorResponseExampleSerializer,
    },
    description="Get business verification status",
    tags=["Business Verification"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def get_business_verification_status(request: Request) -> Response:
    business_verification_repository = get_business_verification_repository()
    verification = business_verification_repository.get_by_user_id(request.user.id)

    if not verification:
        raise NotFound("Business verification not found")

    response_serializer = BusinessVerificationResponseSerializer(verification)

    return StandardResponse.success(
        data=response_serializer.data,
        message="Business verification status retrieved successfully",
    )


@extend_schema(
    request=None,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Verify business email address.",
    tags=["Business Verification"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def verify_business_email(
    request: Request, verification_uuid: str, verification_token: str
) -> Response:
    verify_business_email_rule = get_verify_business_email_rule()
    verify_business_email_rule(
        verification_uuid,
        verification_token,
        event=BusinessEmailVerificationSuccessfulEvent,
    )

    return StandardResponse.success(
        message="Business email verification successful. Welcome to Housing & Properties!"
    )


@extend_schema(
    request=BusinessEmailVerificationRequestSerializer,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Request business email address verification.",
    tags=["Business Verification"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def verify_business_email_request(request: Request) -> Response:
    serializer = BusinessEmailVerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    business_email_verification_rule = get_business_email_verification_request_rule()
    business_email_verification_rule(
        serializer.validated_data["business_email"],
        request.user.id,
        event=BusinessEmailVerificationRequestedEvent,
    )

    return StandardResponse.success(
        message="A new verification link has been sent to your business email."
    )

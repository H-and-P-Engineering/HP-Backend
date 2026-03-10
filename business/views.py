from adrf.decorators import api_view
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.exceptions import NotFound

from core.responses import StandardResponse
from core.serializers import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)
from .serializers import (
    BusinessEmailVerificationRequestSerializer,
    BusinessProfileCreationSerializer,
    BusinessProfileResponseSerializer,
    BusinessVerificationInitiationSerializer,
    BusinessVerificationResponseSerializer,
)
from core.container import container


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
async def create_business_profile(request: Request) -> Response:
    serializer = BusinessProfileCreationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    profile = await container.business_profile_service().create_profile(
        user_id=request.user.id,
        business_name=validated_data["business_name"],
        business_email=validated_data["business_email"],
        registration_number=validated_data["registration_number"],
        address=validated_data.get("address"),
        phone_number=validated_data.get("phone_number"),
        website=validated_data.get("website"),
    )

    response_serializer = BusinessProfileResponseSerializer(profile)

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
async def verify_business(request: Request) -> Response:
    serializer = BusinessVerificationInitiationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    verification = (
        await container.business_verification_service().initiate_verification(
            user_id=request.user.id,
            country_code=validated_data["country_code"],
        )
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
async def get_business_verification_status(request: Request) -> Response:
    verification = (
        await container.business_verification_service().get_verification_status(
            request.user.id
        )
    )

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
async def verify_business_email(
    request: Request, user_uuid: str, verification_token: str
) -> Response:
    await container.business_verification_service().verify_business_email(
        user_uuid, verification_token
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
async def request_business_email_verification(request: Request) -> Response:
    serializer = BusinessEmailVerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    await container.business_verification_service().send_business_email_verification(
        user_id=request.user.id,
    )

    return StandardResponse.success(
        message="A new verification link has been sent to your business email."
    )

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from app.infrastructure.users.events import UserUpdateEvent
from app.presentation.factory import get_update_user_type_rule, get_update_data_rule
from app.presentation.responses import StandardResponse
from app.presentation.serializers.examples import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)
from app.presentation.serializers.users import (
    UpdateSocialRegistrationDataSerializer,
    UpdateUserTypeSerializer,
    UserResponseSerializer,
)


@extend_schema(
    request=UpdateUserTypeSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Update user tye for a registered user.",
    tags=["Users"],
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def update_user_type(request: Request) -> Response:
    serializer = UpdateUserTypeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    user_type_update_rule = get_update_user_type_rule()
    user_type_update_rule(**validated_data, event=UserUpdateEvent)

    return StandardResponse.updated(
        message="User Type update successful.",
    )


@extend_schema(
    request=UpdateSocialRegistrationDataSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Update user data after social registration.",
    tags=["Users"],
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def update_social_registration_data(request: Request) -> Response:
    serializer = UpdateSocialRegistrationDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    social_registration_update_rule = get_update_data_rule()
    user = social_registration_update_rule(
        user_id=request.user.id,
        event=UserUpdateEvent,
        user_type=validated_data["user_type"],
        phone_number=validated_data["phone_number"],
        password=validated_data["password"],
    )

    response_serializer = UserResponseSerializer(dict(user=user))

    return StandardResponse.updated(
        data=response_serializer.data,
        message="Social registration data update successful.",
    )

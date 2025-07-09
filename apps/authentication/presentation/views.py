from typing import Any

from django.views.decorators import cache, csrf
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from social_django.utils import psa

from apps.authentication.infrastructure.factory import (
    get_jwt_token_service,
    get_login_user_rule,
    get_logout_user_rule,
    get_register_user_rule,
    get_request_email_verification_rule,
    get_social_authentication_rule,
    get_update_user_type_rule,
    get_verify_email_rule,
)
from apps.authentication.presentation.serializers import (
    EmailVerificationRequestSerializer,
    JWTTokenSerializer,
    UpdateUserTypeSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    UserRegistrationSerializer,
)
from core.presentation.responses import StandardResponse
from core.presentation.serializers import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)


@extend_schema(
    request=UserRegistrationSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Register a new user.",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def register_user(request: Request) -> Response:
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    register_user_rule = get_register_user_rule()
    user = register_user_rule.execute(**validated_data)

    jwt_token_service = get_jwt_token_service()
    tokens = jwt_token_service.create_tokens(user)

    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))

    return StandardResponse.created(
        data=response_serializer.data,
        message="Registration successful. Check your email for a verification link.",
    )


@extend_schema(
    request=UpdateUserTypeSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Update user tye for a registered user.",
    tags=["Authentication"],
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def update_user_type(request: Request) -> Response:
    serializer = UpdateUserTypeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    user_type_update_rule = get_update_user_type_rule()
    user_type_update_rule.execute(**validated_data)

    return StandardResponse.updated(
        message="User Type update successful.",
    )


@extend_schema(
    request=EmailVerificationRequestSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Request email verification for a registered user.",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def verify_email_request(request: Request) -> Response:
    serializer = EmailVerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    request_email_verification_rule = get_request_email_verification_rule()
    request_email_verification_rule.execute(email=serializer.validated_data["email"])

    return StandardResponse.success(
        message="A new verification link has been sent to your email."
    )


@extend_schema(
    request=None,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Verify email address.",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def verify_email(request: Request, user_uuid: str, verification_token: str) -> Response:
    verify_email_rule = get_verify_email_rule()
    verify_email_rule.execute(user_uuid, verification_token)

    return StandardResponse.success(
        message="Email verification successful. Welcome to Housing & Properties!"
    )


@extend_schema(
    request=UserLoginSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Login an existing user.",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def login_user(request: Request) -> Response:
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    login_user_rule = get_login_user_rule()
    user = login_user_rule.execute(**validated_data)

    jwt_token_service = get_jwt_token_service()
    tokens = jwt_token_service.create_tokens(user)

    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))

    return StandardResponse.success(
        data=response_serializer.data,
        message="Login successful. Welcome back!",
    )


@extend_schema(
    request=UserLogoutSerializer,
    responses={
        201: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Logout an authenticated user.",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def logout_user(request: Request) -> Response:
    serializer = UserLogoutSerializer(data=request.data, context={"user": request.user})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    logout_user_rule = get_logout_user_rule()
    logout_user_rule.execute(**validated_data)

    return StandardResponse.success(message="Logout successful.")


@extend_schema(
    request=None,
    responses={
        301: None,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Begin social authentication.",
    tags=["Authentication"],
)
@csrf.csrf_exempt
@cache.never_cache
@psa("authentication:social-complete")
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def begin_social_authentication(request: Request, backend_name: str) -> Any:
    user_type = request.query_params.get("user_type", "CLIENT")

    social_authentication_rule = get_social_authentication_rule()
    return social_authentication_rule.begin_authentication(
        request=request
    )


@extend_schema(
    request=None,
    responses={
        "200-201": SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Complete social authentication.",
    tags=["Authentication"],
)
@csrf.csrf_exempt
@cache.never_cache
@psa("authentication:social-complete")
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def complete_social_authentication(request: Request, backend_name: str) -> Response:
    social_authentication_rule = get_social_authentication_rule()

    user_dict = social_authentication_rule.complete_authentication(request)
    user = user_dict["user"]

    jwt_token_service = get_jwt_token_service()
    tokens = jwt_token_service.create_tokens(user)
    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))

    is_new_user = user_dict["is_new_user"]

    if is_new_user:
        return StandardResponse.created(
            data=response_serializer.data,
            message="Registration successful. Welcome to Housing & Properties!",
        )
    else:
        return StandardResponse.success(
            data=response_serializer.data,
            message="Login successful. Welcome back!",
        )

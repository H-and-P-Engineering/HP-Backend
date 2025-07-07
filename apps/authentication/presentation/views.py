from typing import Any

from django.db import transaction
from django.views.decorators import cache, csrf
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from social_django.utils import psa

from apps.authentication.application.rules import (
    LoginUserRule,
    LogoutUserRule,
    RegisterUserRule,
    RequestEmailVerificationRule,
    SocialAuthenticationRule,
    VerifyEmailRule,
)
from apps.authentication.infrastructure.repositories import (
    DjangoBlackListedTokenRepository,
)
from apps.authentication.infrastructure.services import (
    DjangoCacheServiceAdapter,
    DjangoEmailServiceAdapter,
    DjangoJWTTokenAdapter,
    DjangoPasswordServiceAdapter,
    DjangoVerificationServiceAdapter,
    SocialAuthenticationAdapter,
)
from apps.authentication.presentation.serializers import (
    EmailVerificationRequestSerializer,
    JWTTokenSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    UserRegistrationSerializer,
)
from apps.users.infrastructure.repositories import DjangoUserRepository
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

    user_repository = DjangoUserRepository()
    password_service = DjangoPasswordServiceAdapter()
    verification_service = DjangoVerificationServiceAdapter()
    cache_service = DjangoCacheServiceAdapter()
    email_service = DjangoEmailServiceAdapter()
    jwt_token_service = DjangoJWTTokenAdapter()

    register_user_rule = RegisterUserRule(user_repository, password_service)

    request_email_verification_rule = RequestEmailVerificationRule(
        verification_service, cache_service, email_service
    )

    with transaction.atomic():
        user = register_user_rule.execute(**validated_data)
        request_email_verification_rule.execute(user)

    tokens = jwt_token_service.create_tokens(user)

    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))

    return StandardResponse.created(
        data=response_serializer.data,
        message="Registration successful. Check your email for a verification link.",
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

    validated_data = serializer.validated_data

    user_repository = DjangoUserRepository()
    verification_service = DjangoVerificationServiceAdapter()
    cache_service = DjangoCacheServiceAdapter()
    email_service = DjangoEmailServiceAdapter()

    request_email_verification_rule = RequestEmailVerificationRule(
        verification_service, cache_service, email_service
    )

    user = user_repository.get_by_email(**validated_data)

    request_email_verification_rule.execute(user)

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
    user_repository = DjangoUserRepository()
    email_service = DjangoEmailServiceAdapter()
    verification_service = DjangoVerificationServiceAdapter()
    cache_service = DjangoCacheServiceAdapter()

    verify_email_rule = VerifyEmailRule(
        user_repository, email_service, verification_service, cache_service
    )

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

    user_repository = DjangoUserRepository()
    password_service = DjangoPasswordServiceAdapter()
    jwt_token_service = DjangoJWTTokenAdapter()

    login_user_rule = LoginUserRule(
        user_repository,
        password_service,
    )

    user = login_user_rule.execute(**validated_data)

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

    blacklisted_token_repository = DjangoBlackListedTokenRepository()
    jwt_token_service = DjangoJWTTokenAdapter()

    logout_user_rule = LogoutUserRule(
        blacklisted_token_repository,
        jwt_token_service,
    )
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

    social_authentication_service = SocialAuthenticationAdapter()

    social_authentication_rule = SocialAuthenticationRule(
        social_authentication_service=social_authentication_service
    )
    return social_authentication_rule.begin_authentication(
        request=request, user_type=user_type
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
    social_authentication_service = SocialAuthenticationAdapter()
    user_repository = DjangoUserRepository()
    jwt_token_service = DjangoJWTTokenAdapter()

    social_authentication_rule = SocialAuthenticationRule(
        social_authentication_service=social_authentication_service,
        user_repository=user_repository,
    )

    user = social_authentication_rule.complete_authentication(request)

    tokens = jwt_token_service.create_tokens(user)

    response_serializer = JWTTokenSerializer(dict(user=user, **tokens))

    is_new_user = getattr(user, "is_new")

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

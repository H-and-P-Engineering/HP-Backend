from asgiref.sync import async_to_sync
from typing import Any

from adrf.decorators import api_view
from django.views.decorators import cache, csrf
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.http import HttpResponse
from social_django.utils import psa

from core.responses import StandardResponse
from core.serializers import (
    ErrorResponseExampleSerializer,
    SuccessResponseExampleSerializer,
)
from .serializers import (
    EmailVerificationRequestSerializer,
    EmailVerificationSerializer,
    UserRegistrationSerializer,
    UserResponseSerializer,
    UserLoginSerializer,
    JWTTokenSerializer,
    UserLogoutSerializer,
    UpdateUserDataSerializer,
)
from core.container import container


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
async def register_user(request: Request) -> Response:
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    user = await container.user_service().create(**validated_data)

    container.user_service().send_email_verification(user)

    response_serializer = UserResponseSerializer(user)

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
async def request_email_verification(request: Request) -> Response:
    serializer = EmailVerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    user = await container.user_service().fetch_user_for_verification(email)

    container.user_service().send_email_verification(user)

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
async def verify_email(
    request: Request, user_uuid: str, verification_token: str
) -> Response:
    serializer = EmailVerificationSerializer(
        data={"user_uuid": user_uuid, "verification_token": verification_token}
    )
    serializer.is_valid(raise_exception=True)

    validated_data = serializer.validated_data

    user = await container.user_service().validate_and_verify_email(
        user_uuid=validated_data["user_uuid"],
        verification_token=validated_data["verification_token"],
    )

    response_serializer = UserResponseSerializer(user)

    return StandardResponse.success(
        message="Email verification successful. Welcome to Housing & Properties!",
        data=response_serializer.data,
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
async def login_user(request: Request) -> Response:
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    user, tokens = await container.authentication_service().login(**validated_data)

    user_serializer = UserResponseSerializer(dict(is_new=False, **user.__dict__))

    response_serializer = JWTTokenSerializer(dict(user=user_serializer.data, **tokens))

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
async def logout_user(request: Request) -> Response:
    serializer = UserLogoutSerializer(data=request.data, context={"user": request.user})
    serializer.is_valid(raise_exception=True)

    container.authentication_service().logout(request.user.id)

    return StandardResponse.success(message="Logout successful.")


@extend_schema(
    request=None,
    responses={
        302: None,
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
    user_type = request.query_params.get("user_type", "BUYER")

    async_to_sync(container.authentication_service().blacklist_auth_token)(
        auth_header=request.headers.get("Authorization")
    )

    return container.authentication_service().begin_social_auth(request, user_type)


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
    user, tokens = async_to_sync(
        container.authentication_service().complete_authentication
    )(request)
    user_serializer = UserResponseSerializer(user)

    orchestration = (
        container.authentication_service().orchestrate_social_login_response(
            user=user, tokens=tokens, user_data=user_serializer.data
        )
    )

    redirect_url = orchestration["redirect_url"]
    session_id = orchestration["session_id"]
    response_data = orchestration["response_data"]

    if redirect_url:
        response = HttpResponse(status=303)
        response["Location"] = redirect_url
        response.set_cookie(
            "social_auth_session",
            session_id,
            max_age=600,
            httponly=True,
            secure=True,
            samesite="None",
        )
        return response

    return StandardResponse.success(
        data=response_data,
        message=response_data.pop("message", None),
    )


@extend_schema(
    request=None,
    responses={
        200: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Fetch social authentication user data using temporary session ID.",
    tags=["Authentication"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
async def get_social_auth_data(request: Request) -> Response:
    session_id = request.COOKIES.get("social_auth_session")
    container.authentication_service().verify_social_session_data(session_id)

    auth_data = container.social_cache_service().get(session_id)
    container.authentication_service().verify_social_session_data(auth_data)

    container.social_cache_service().delete(session_id)

    message = auth_data.pop("message", "Login successful. Welcome back!")

    response = StandardResponse.success(data=auth_data, message=message)
    response.delete_cookie("social_auth_session")
    return response


@extend_schema(
    request=UpdateUserDataSerializer,
    responses={
        202: SuccessResponseExampleSerializer,
        400: ErrorResponseExampleSerializer,
        500: ErrorResponseExampleSerializer,
    },
    description="Update user data for a registered user.",
    tags=["Users"],
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
async def update_user_data(request: Request) -> Response:
    serializer = UpdateUserDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data

    await container.user_service().update(
        user_uuid=request.user.uuid, update_data=validated_data
    )

    return StandardResponse.updated(
        message="User data updated successfully.",
    )

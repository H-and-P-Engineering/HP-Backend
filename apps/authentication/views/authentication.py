from typing import Any

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django.utils import psa

from apps.authentication.serializers import (
    ErrorResponseExampleSerializer,
    TokenSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from apps.authentication.services import authentication_service
from core.utils.responses import StandardResponse


class RegisterView(APIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={201: TokenSerializer, "400 - 500": ErrorResponseExampleSerializer},
        description="Register a new user account via email",
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        """Handle user registration."""

        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user, tokens = authentication_service.register_user(**validated_data)

        response_data = {**tokens, "user": user}
        response_serializer = TokenSerializer(response_data)

        return StandardResponse.created(
            data=response_serializer.data,
            message="Registration successful. Please verify your email.",
        )


class LoginView(APIView):
    """User login endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={200: TokenSerializer, "400 - 500": ErrorResponseExampleSerializer},
        description="Log in to an existing account via email",
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        """Handle user login."""

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        user, tokens = authentication_service.login(**validated_data)

        response_data = {**tokens, "user": user}
        response_serializer = TokenSerializer(response_data)

        return StandardResponse.success(
            data=response_serializer.data,
            message="Login successful. Welcome back!",
        )


class EmailVerificationView(APIView):
    """Email verification endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={
            200: {"message": "string"},
            "400 - 500": ErrorResponseExampleSerializer,
        },
        description="Verify email address",
        tags=["Authentication"],
    )
    def post(self, request: Request, user_id: str, verification_token: str) -> Response:
        """Handle email verification."""

        authentication_service.verify_email(user_id=user_id, token=verification_token)

        return StandardResponse.success(
            message="Email verification successful. Welcome to Housing & Properties!"
        )


@method_decorator(
    [csrf_exempt, never_cache, psa("authentication:social-complete")], name="get"
)
class SocialAuthenticationBeginView(APIView):
    """Social authentication initiation endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={
            301: None,
            "400 - 500": ErrorResponseExampleSerializer,
        },
        description="Begin social authentication",
        tags=["Authentication"],
    )
    def get(self, request: Request, backend: str) -> Any:
        """Handle social authentication initiation."""

        user_type = request.query_params.get("user_type", "CLIENT")

        return authentication_service.begin_social_authentication(
            request, backend, user_type
        )


@method_decorator(
    [csrf_exempt, never_cache, psa("authentication:social-complete")], name="get"
)
class SocialAuthenticationCompleteView(APIView):
    """Social authentication completion endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            "200 - 201": TokenSerializer,
            "400 - 500": ErrorResponseExampleSerializer,
        },
        description="Register a new user account via social backends",
        tags=["Authentication"],
    )
    def get(self, request, backend):
        """Handle social authentication completion."""

        user, tokens = authentication_service.complete_social_authentication(
            request, backend
        )

        response_data = {**tokens, "user": user}
        response_serializer = TokenSerializer(response_data)

        is_new = getattr(user, "is_new", False)

        if is_new:
            return StandardResponse.created(
                data=response_serializer.data,
                message="Social authentication successful. Welcome to Housing & Properties!",
            )
        else:
            return StandardResponse.success(
                data=response_serializer.data, message="Login successful. Welcome back!"
            )

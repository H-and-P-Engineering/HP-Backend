from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
        try:
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
        except Exception as e:
            raise e


class LoginView(APIView):
    """User login endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=UserLoginSerializer,
        responses={201: TokenSerializer, "400 - 500": ErrorResponseExampleSerializer},
        description="Log in to an existing account via email",
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        """Handle user login."""

        try:
            serializer = UserLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            user, tokens = authentication_service.login(**validated_data)
            response_data = {**tokens, "user": user}

            response_serializer = TokenSerializer(response_data)

            return StandardResponse.success(
                data=response_serializer.data,
                message="Login successful.",
            )
        except Exception as e:
            raise e


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

        return StandardResponse.success(message="Email verification successful.")

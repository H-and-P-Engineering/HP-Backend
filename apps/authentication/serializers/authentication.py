from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""

    email = serializers.EmailField(required=True)

    password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        style={"input_type": "password"},
        help_text="Password must be at least 8 characters",
    )

    user_type = serializers.ChoiceField(
        required=True,
        choices=User.UserType.choices,
        help_text="Type of account to create",
    )

    first_name = serializers.CharField(required=True, max_length=30)

    last_name = serializers.CharField(required=True, max_length=30)


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )


class TokenSerializer(serializers.Serializer):
    """
    Serializer for JWT token response.

    This is a read-only serializer that formats the response
    from the authentication service.
    """

    access = serializers.CharField(read_only=True, help_text="JWT access token")

    refresh = serializers.CharField(read_only=True, help_text="JWT refresh token")

    user = serializers.SerializerMethodField(help_text="Basic user information")

    def get_user(self, obj: dict[str, Any]) -> dict[str, Any]:
        """Format user data for response."""

        user = obj.get("user")
        if user:
            return {
                "id": str(user.uuid),
                "email": user.email,
                "user_type": user.user_type,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_email_verified,
            }
        return {}


class ErrorResponseExampleSerializer(serializers.Serializer):
    """Serializer representing error response schema for OpenApi."""

    success = serializers.BooleanField(read_only=True, default=False)
    message = serializers.CharField(read_only=True)
    errors = serializers.DictField(read_only=True)
    status_code = serializers.IntegerField(read_only=True)

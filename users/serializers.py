import re
from typing import Any

from adrf.serializers import Serializer
from rest_framework import serializers

from .models import UserType


def validate_password_value(value: str) -> str:
    if " " in value:
        raise serializers.ValidationError("Password must not contain spaces.")

    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one digit.")

    if not re.search(r"[!@#$%^&*(),.?\"\'{}|<>]", value):
        raise serializers.ValidationError(
            "Password must contain at least one special character."
        )

    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )

    return value


def validate_phone_number_value(value: str) -> str:
    if " " in value:
        raise serializers.ValidationError("Phone number must not contain spaces.")

    if not re.search(r"^\+?[1-9]\d{7,14}$", value):
        raise serializers.ValidationError(
            "Phone number must be at least 8 digits long and can contain country code."
        )

    return value


class UserRegistrationSerializer(Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    user_type = serializers.ChoiceField(
        allow_blank=True,
        choices=UserType.choices(),
        default=UserType.BUYER.value,
    )
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    phone_number = serializers.CharField(required=True, max_length=20)

    def validate_password(self, value: str) -> str:
        return validate_password_value(value)


class EmailVerificationRequestSerializer(Serializer):
    email = serializers.EmailField(required=True)


class EmailVerificationSerializer(Serializer):
    user_uuid = serializers.UUIDField(required=True)
    verification_token = serializers.CharField(required=True, max_length=120)


class UserResponseSerializer(Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    is_new = serializers.BooleanField(default=True)


class UserLoginSerializer(Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class JWTTokenSerializer(Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserResponseSerializer(read_only=True)


class UserLogoutSerializer(Serializer):
    user_id = serializers.IntegerField(read_only=True)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user = self.context.get("user")
        if not user or not hasattr(user, "id"):
            raise serializers.ValidationError("User data is required for logout.")

        data["user_id"] = user.id
        return data


class UpdateUserDataSerializer(Serializer):
    user_type = serializers.ChoiceField(required=False, choices=UserType.choices())
    phone_number = serializers.CharField(max_length=20, required=False)
    password = serializers.CharField(required=False)

    def validate_user_type(self, value: str | None) -> str | None:
        if value and value == "ADMIN":
            raise serializers.ValidationError(
                "User type for regular users cannot be 'ADMIN'."
            )

        return value

    def validate_password(self, value: str | None) -> str | None:
        if value:
            return validate_password_value(value)

    def validate_phone_number(self, value: str | None) -> str | None:
        if value:
            return validate_phone_number_value(value)

import re
from typing import Any, Dict

from rest_framework import serializers

from apps.users.domain.enums import UserType as DomainUserType
from apps.users.domain.models import User as DomainUser


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    user_type = serializers.ChoiceField(
        allow_blank=True,
        choices=DomainUserType.choices(),
        default=DomainUserType.CLIENT,
    )
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    phone_number = serializers.CharField(required=True, max_length=20)

    def validate_password(self, value: str) -> str:
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
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )

        if not re.search(r"[!@#$%^&*(),.?\"\'{}|<>]", value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        return value


class UpdateUserTypeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    user_type = serializers.ChoiceField(required=True, choices=DomainUserType.choices())

    def validate_user_type(self, value: str) -> str:
        if value == "ADMIN":
            raise serializers.ValidationError(
                "User type for regular users cannot be 'ADMIN'."
            )

        return value


class EmailVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class JWTTokenSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()

    def get_user(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        user: DomainUser = obj.get("user")
        if user:
            return {
                "id": str(user.uuid),
                "email": user.email,
                "user_type": user.user_type.value
                if hasattr(user.user_type, "value")
                else user.user_type,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "is_email_verified": user.is_email_verified,
                "is_new": user.is_new,
            }
        return {}


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserLogoutSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    user_id = serializers.IntegerField(read_only=True)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user = self.context.get("user")
        if not user or not hasattr(user, "id"):
            raise serializers.ValidationError("User context is required for logout.")

        data["user_id"] = user.id
        return data

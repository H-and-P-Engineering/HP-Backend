from typing import Any, Dict

from app.infrastructure.password_service import validate_password_value
from rest_framework import serializers

from app.domain.users.entities import User as DomainUser
from app.domain.users.enums import UserType as DomainUserType


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    user_type = serializers.ChoiceField(
        allow_blank=True,
        choices=DomainUserType.choices(),
        default=DomainUserType.BUYER.value,
    )
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    phone_number = serializers.CharField(required=True, max_length=20)

    def validate_password(self, value: str) -> str:
        validate_password_value(value)

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
                "id": user.id,
                "email": user.email,
                "user_type": (
                    user.user_type.value
                    if hasattr(user.user_type, "value")
                    else user.user_type
                ),
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

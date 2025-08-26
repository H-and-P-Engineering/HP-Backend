from typing import Any, Dict

from app.infrastructure.password_service import validate_password_value
from rest_framework import serializers

from app.domain.users.entities import User as DomainUser
from app.domain.users.enums import UserType as DomainUserType


class UserResponseSerializer(serializers.Serializer):
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


class UpdateUserTypeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    user_type = serializers.ChoiceField(required=True, choices=DomainUserType.choices())

    def validate_user_type(self, value: str) -> str:
        if value == "ADMIN":
            raise serializers.ValidationError(
                "User type for regular users cannot be 'ADMIN'."
            )

        return value


class UpdateSocialRegistrationDataSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(required=True)

    def validate_password(self, value: str) -> str:
        validate_password_value(value)

        return value

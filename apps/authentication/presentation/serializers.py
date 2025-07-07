from typing import Any, Dict

from rest_framework import serializers

from apps.users.domain.enums import UserType
from apps.users.domain.models import User as DomainUser


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    user_type = serializers.ChoiceField(required=True, choices=UserType.choices())
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)


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
                "user_type": user.user_type,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_email_verified": user.is_email_verified,
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

        data["user_id"] = user.id

        return data

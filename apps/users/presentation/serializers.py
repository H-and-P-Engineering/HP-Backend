from typing import Any, Dict

from rest_framework import serializers

from apps.users.domain.models import User as DomainUser


class UserResponseSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        user: DomainUser = obj.get("user")
        if user:
            return {
                "id": str(user.uuid),
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

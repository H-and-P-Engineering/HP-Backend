from rest_framework import serializers


class BusinessProfileCreationSerializer(serializers.Serializer):
    business_name = serializers.CharField(required=True, max_length=255)
    registration_number = serializers.CharField(required=True, max_length=50)
    country_code = serializers.CharField(required=True, max_length=10)
    business_email = serializers.EmailField(required=True, max_length=255)
    address = serializers.CharField(required=False, allow_blank=True, max_length=500)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, max_length=20
    )
    website = serializers.URLField(required=False, allow_blank=True, max_length=255)

    def validate_registration_number(self, value: str) -> str:
        if not value.replace("-", "").replace(" ", "").isalnum():
            raise serializers.ValidationError(
                "Registration number must be alphanumeric."
            )

        value = value.upper().strip()

        valid_prefixes = ["RC", "BN", "IT", "LP", "LLP"]

        if not any(value.startswith(prefix) for prefix in valid_prefixes):
            raise serializers.ValidationError(
                "Registration number must start with a valid prefix (e.g., 'RC', 'BN', 'IT', 'LP', 'LLP')."
            )

        return value


class BusinessProfileResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    business_name = serializers.CharField(max_length=255)
    registration_number = serializers.CharField(max_length=50)
    is_business_email_verified = serializers.BooleanField(default=False)
    verification_id = serializers.IntegerField(required=False, allow_null=True)
    business_email = serializers.EmailField(max_length=255)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    phone_number = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    website = serializers.URLField(max_length=255, required=False, allow_blank=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class BusinessVerificationInitiationSerializer(serializers.Serializer):
    country_code = serializers.CharField(required=False, default="NG", max_length=10)


class BusinessVerificationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    business_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    business_email = serializers.EmailField(
        max_length=255, required=False, allow_blank=True
    )
    business_registration_number = serializers.CharField(max_length=100)
    country_code = serializers.CharField(max_length=10, default="NG")
    verification_provider_reference = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    verification_status = serializers.CharField(max_length=12)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class BusinessEmailVerificationRequestSerializer(serializers.Serializer):
    business_email = serializers.EmailField(required=True)

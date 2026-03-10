from enum import StrEnum

import uuid6
from django.db import models

from users.models import User


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    SUCCESSFUL = "SUCCESSFUL"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.name) for member in cls]

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class BusinessVerification(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="business_verification"
    )
    business_registration_number = models.CharField(max_length=100)
    business_name = models.CharField(max_length=255, null=True, blank=True)
    business_email = models.EmailField(null=True, blank=True)
    country_code = models.CharField(max_length=10, default="NG")
    verification_provider = models.CharField(max_length=100, null=True, blank=True)
    verification_provider_reference = models.CharField(
        max_length=100, null=True, blank=True
    )
    verification_status = models.CharField(
        max_length=12,
        choices=VerificationStatus.choices(),
        default=VerificationStatus.PENDING,
    )
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_verifications"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["business_registration_number"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self) -> str:
        return f"Verification for {self.business_name} ({self.business_registration_number})"


class BusinessProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="business_profile"
    )
    business_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    business_email = models.EmailField(max_length=255, unique=True)
    website = models.URLField(null=True, blank=True)
    verification = models.OneToOneField(
        BusinessVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="business_profile",
    )
    is_business_email_verified = models.BooleanField(default=False)
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["business_name"]),
            models.Index(fields=["business_email"]),
            models.Index(fields=["registration_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.business_name} ({self.registration_number})"

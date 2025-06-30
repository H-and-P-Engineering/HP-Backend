import uuid6
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.authentication.domain.models import UserType
from apps.authentication.infrastructure.managers import UserManager


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    username = None
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        max_length=16, choices=UserType.choices, default=UserType.CLIENT
    )
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["is_email_verified"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user_type", "is_active"]),
            models.Index(fields=["is_email_verified", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.email


class BlackListedToken(models.Model):
    access = models.TextField(unique=True)
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="blacklisted_tokens",
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_blacklisted_tokens"
        verbose_name = "Blacklisted Token"
        verbose_name_plural = "Blacklisted Tokens"
        indexes = [
            models.Index(fields=["access"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"Token {self.access[:20]}... for {str(self.user)} (blacklisted at {self.created_at})"

    @classmethod
    def is_blacklisted(cls, access_token: str) -> bool:
        return cls.objects.filter(access=access_token).exists()

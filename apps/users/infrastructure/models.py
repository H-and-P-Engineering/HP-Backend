import uuid6
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.domain.enums import UserType
from apps.users.infrastructure.managers import UserManager


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
        return str(self.email)

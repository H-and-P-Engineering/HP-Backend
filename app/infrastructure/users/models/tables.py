import uuid6
from django.contrib.auth.models import AbstractUser
from django.db import models

from app.domain.users.enums import UserType as DomainUserType

from ..managers import UserManager


class User(AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid6.uuid7, editable=False)
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    user_type = models.CharField(
        max_length=16, choices=DomainUserType.choices, default=DomainUserType.CLIENT
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
        constraints = [
            models.UniqueConstraint(
                fields=["phone_number"],
                condition=models.Q(phone_number__isnull=False)
                & ~models.Q(phone_number=""),
                name="unique_phone_number_constraint",
            ),
        ]

    def __str__(self) -> str:
        return str(self.email)

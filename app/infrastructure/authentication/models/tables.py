from django.db import models


class BlackListedToken(models.Model):
    access = models.TextField(unique=True)
    user = models.ForeignKey(
        "users.User",
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

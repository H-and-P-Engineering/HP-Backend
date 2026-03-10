from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BlackListedToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_email_verified",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = (
        "user_type",
        "is_email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name", "phone_number", "uuid")
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at", "updated_at", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name", "phone_number", "user_type")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_email_verified",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "uuid",
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "user_type",
                ),
            },
        ),
    )


@admin.register(BlackListedToken)
class BlackListedTokenAdmin(admin.ModelAdmin):
    list_display = ("truncated_token", "user", "expires_at", "created_at")
    list_filter = ("expires_at", "created_at")
    search_fields = ("access", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("access", "user", "expires_at", "created_at")

    def truncated_token(self, obj: BlackListedToken) -> str:
        return f"{obj.access[:30]}..."

    truncated_token.short_description = "Token"

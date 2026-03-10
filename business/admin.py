from django.contrib import admin
from django.utils.html import format_html

from .models import BusinessProfile, BusinessVerification, VerificationStatus


@admin.register(BusinessVerification)
class BusinessVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "business_registration_number",
        "user",
        "verification_status_badge",
        "verification_provider",
        "country_code",
        "created_at",
    )
    list_filter = (
        "verification_status",
        "verification_provider",
        "country_code",
        "created_at",
    )
    search_fields = (
        "business_name",
        "business_registration_number",
        "business_email",
        "user__email",
        "uuid",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "verification_provider_reference",
    )

    fieldsets = (
        (
            "Business Info",
            {
                "fields": (
                    "user",
                    "business_name",
                    "business_registration_number",
                    "business_email",
                    "country_code",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "verification_status",
                    "verification_provider",
                    "verification_provider_reference",
                )
            },
        ),
        ("Metadata", {"fields": ("uuid", "created_at", "updated_at")}),
    )

    def verification_status_badge(self, obj: BusinessVerification) -> str:
        colors = {
            VerificationStatus.PENDING: "#f0ad4e",
            VerificationStatus.IN_PROGRESS: "#5bc0de",
            VerificationStatus.FAILED: "#d9534f",
            VerificationStatus.SUCCESSFUL: "#5cb85c",
        }
        color = colors.get(obj.verification_status, "#777")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.verification_status,
        )

    verification_status_badge.short_description = "Status"


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "registration_number",
        "user",
        "business_email",
        "is_business_email_verified",
        "has_verification",
        "created_at",
    )
    list_filter = (
        "is_business_email_verified",
        "created_at",
    )
    search_fields = (
        "business_name",
        "registration_number",
        "business_email",
        "user__email",
        "uuid",
    )
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("user", "verification")

    fieldsets = (
        (
            "Business Info",
            {
                "fields": (
                    "user",
                    "business_name",
                    "registration_number",
                    "business_email",
                    "phone_number",
                    "address",
                    "website",
                )
            },
        ),
        (
            "Verification",
            {"fields": ("verification", "is_business_email_verified")},
        ),
        ("Metadata", {"fields": ("uuid", "created_at", "updated_at")}),
    )

    def has_verification(self, obj: BusinessProfile) -> bool:
        return obj.verification is not None

    has_verification.boolean = True
    has_verification.short_description = "Verified"

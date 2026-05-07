from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailVerificationCode, User


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "expires_at", "used_at", "created_at")
    list_filter = ("used_at", "expires_at")
    search_fields = ("user__email", "user__username", "code")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "is_email_verified",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_email_verified",
        "groups",
    )
    search_fields = ("email", "username", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "avatar", "bio", "geodata")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_email_verified",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    autocomplete_fields = ("geodata",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "is_email_verified",
                ),
            },
        ),
    )

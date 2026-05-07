from django.contrib import admin

from .models import (
    Category,
    Event,
    EventImage,
    Organization,
    OrganizationMember,
    OrganizationNews,
    OrganizationNewsComment,
    OrganizationRegistrationRequest,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "official_name",
        "created_by",
        "email",
        "phone",
        "website_url",
        "vk_url",
        "max_url",
        "executive_person_full_name",
        "created_at",
    )
    search_fields = (
        "official_name",
        "email",
        "phone",
        "website_url",
        "vk_url",
        "max_url",
        "executive_person_full_name",
        "executive_body_name",
    )
    list_filter = ("created_at",)
    autocomplete_fields = ("created_by",)
    inlines = (OrganizationMemberInline,)


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("organization__official_name", "user__email", "user__username")
    autocomplete_fields = ("organization", "user")


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 3
    fields = ("image", "alt_text", "sort_order", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "category", "status", "starts_at", "is_online")
    list_filter = ("status", "category", "is_online", "starts_at")
    search_fields = ("title", "content", "organization__official_name")
    autocomplete_fields = ("category", "organization", "created_by_member", "geodata")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (EventImageInline,)


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ("event", "image", "sort_order", "created_at")
    list_filter = ("created_at",)
    search_fields = ("event__title", "alt_text", "image")
    autocomplete_fields = ("event",)


@admin.register(OrganizationNews)
class OrganizationNewsAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "created_by_member", "views_count", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "text", "organization__official_name", "created_by_member__user__email")
    autocomplete_fields = ("organization", "created_by_member")


@admin.register(OrganizationNewsComment)
class OrganizationNewsCommentAdmin(admin.ModelAdmin):
    list_display = ("news", "created_by", "created_at", "updated_at")
    search_fields = ("text", "news__title", "created_by__email")
    autocomplete_fields = ("news", "created_by")


@admin.register(OrganizationRegistrationRequest)
class OrganizationRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "official_name",
        "created_by",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("official_name", "created_by__email", "created_by__username")
    autocomplete_fields = ("created_by", "reviewed_by", "organization")

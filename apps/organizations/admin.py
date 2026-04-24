from django.contrib import admin

from .models import Event, Organization, OrganizationMember, OrganizationRegistrationRequest


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
        "executive_person_full_name",
        "created_at",
    )
    search_fields = (
        "official_name",
        "email",
        "phone",
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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "category", "status", "starts_at", "is_online")
    list_filter = ("status", "category", "is_online", "starts_at")
    search_fields = ("title", "content", "organization__official_name")
    autocomplete_fields = ("category", "organization", "created_by_member")
    prepopulated_fields = {"slug": ("title",)}


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

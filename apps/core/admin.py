from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "scope", "slug", "created_at")
    list_filter = ("scope",)
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}

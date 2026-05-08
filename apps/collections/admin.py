from django.contrib import admin

from .models import (
    BranchItem,
    Collection,
    CollectionItem,
    CourierProfile,
    DonorGroup,
    DonorGroupItem,
    DonorGroupMember,
    Item,
    ItemCategory,
    UserItem,
)


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "is_active", "created_at")
    list_filter = ("unit", "is_active")
    search_fields = ("name",)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description", "category__name")


@admin.register(UserItem)
class UserItemAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "quantity", "created_at")
    list_filter = ("category",)
    search_fields = ("user__email", "category__name", "description")


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 0


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "status", "created_by_member", "created_at")
    list_filter = ("status", "organization")
    search_fields = ("title", "description", "organization__official_name")
    inlines = (CollectionItemInline,)


@admin.register(CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ("collection", "category", "quantity_required", "created_at")
    list_filter = ("category",)
    search_fields = ("collection__title", "category__name", "description")


@admin.register(BranchItem)
class BranchItemAdmin(admin.ModelAdmin):
    list_display = ("branch", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("branch__name", "category__name", "description")


class DonorGroupMemberInline(admin.TabularInline):
    model = DonorGroupMember
    extra = 0


class DonorGroupItemInline(admin.TabularInline):
    model = DonorGroupItem
    extra = 0


@admin.register(DonorGroup)
class DonorGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "collection", "title", "created_by_member", "created_at")
    search_fields = ("title", "collection__title")
    inlines = (DonorGroupMemberInline, DonorGroupItemInline)


@admin.register(DonorGroupMember)
class DonorGroupMemberAdmin(admin.ModelAdmin):
    list_display = ("donor_group", "user", "joined_at")
    search_fields = ("donor_group__title", "user__email")


@admin.register(DonorGroupItem)
class DonorGroupItemAdmin(admin.ModelAdmin):
    list_display = ("donor_group", "user_item", "quantity", "created_at")
    search_fields = (
        "donor_group__title",
        "user_item__user__email",
        "user_item__category__name",
    )


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "car_name", "created_at")
    search_fields = ("user__email", "car_name")
    autocomplete_fields = ("user",)

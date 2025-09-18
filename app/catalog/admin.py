from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "level")
    list_filter = ("parent",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def level(self, obj):
        return obj.level

    level.short_description = _("level")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "absolute_position",
        "rating",
        "sales_30d",
    )
    list_filter = ("category",)
    search_fields = ("name", "slug")
    list_editable = ("absolute_position", "price")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)

"""Admin for Item."""

from django.contrib import admin

from core.admin import BaseModelAdmin, IdentifierInline
from mdm.models import Item


@admin.register(Item)
class ItemAdmin(BaseModelAdmin):
    list_display = ("name", "sku", "version", "manufacturer")
    search_fields = ("name", "sku", "version")
    list_filter = ("categories", "manufacturer")
    autocomplete_fields = ("manufacturer", "categories", "documents", "related_items")
    list_select_related = ("manufacturer",)
    inlines = [IdentifierInline]
    fieldsets = (
        (None, {"fields": ("name", "sku", "version", "manufacturer")}),
        ("Classification", {"fields": ("categories",)}),
        ("Attributes & pricing", {"fields": ("features", "pricing")}),
        ("Linked records", {"fields": ("documents", "related_items")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

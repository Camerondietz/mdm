"""Admin for Location."""

from django.contrib import admin

from core.admin import BaseModelAdmin, IdentifierInline
from mdm.models import Location


@admin.register(Location)
class LocationAdmin(BaseModelAdmin):
    list_display = ("name", "kind", "address_region", "country_code", "parent")
    list_filter = ("kind", "country_code")
    search_fields = (
        "name",
        "street_address",
        "address_locality",
        "address_region",
        "postal_code",
        "code",
    )
    autocomplete_fields = ("parent",)
    list_select_related = ("parent",)
    inlines = [IdentifierInline]
    fieldsets = (
        (None, {"fields": ("name", "kind", "parent")}),
        (
            "Postal address",
            {
                "fields": (
                    "street_address",
                    ("address_locality", "address_region"),
                    ("postal_code", "country_code"),
                )
            },
        ),
        ("Coordinates & codes", {"fields": (("latitude", "longitude"), "code")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

"""Reusable admin building blocks shared across the MDM domain admin."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from core.models import ContactPoint, Identifier, Relationship


# ── Generic inlines: attach contacts / identifiers to any entity admin ────────
class ContactPointInline(GenericTabularInline):
    model = ContactPoint
    extra = 0
    fields = ("kind", "value", "label", "is_primary")
    classes = ("collapse",)


class IdentifierInline(GenericTabularInline):
    model = Identifier
    extra = 0
    fields = ("scheme", "value", "issuer", "is_primary")
    classes = ("collapse",)


# ── Base admin: consistent, fast editing everywhere ───────────────────────────
class BaseModelAdmin(admin.ModelAdmin):
    """Sensible defaults for every BaseModel-derived admin."""

    save_on_top = True
    list_per_page = 50
    readonly_fields = ("id", "created_at", "updated_at", "uri_display")
    show_facets = admin.ShowFacets.ALWAYS

    # Standard provenance/metadata fieldset admins can append to their fieldsets.
    PROVENANCE_FIELDSET = (
        "Provenance & metadata",
        {
            "classes": ("collapse",),
            "fields": (
                "source_system",
                "source_record_id",
                "metadata",
                ("id", "uri_display"),
                ("created_at", "updated_at"),
            ),
        },
    )

    @admin.display(description="URI (@id)")
    def uri_display(self, obj):
        return obj.get_uri() if obj and obj.pk else "—"


class TaxonomyTermAdmin(admin.ModelAdmin):
    """Base admin for controlled-vocabulary tables."""

    list_display = ("name", "code", "parent", "slug")
    list_filter = ("parent",)
    search_fields = ("name", "code", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)
    list_select_related = ("parent",)
    ordering = ("name",)


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    """
    Advanced tool: create typed subject-predicate-object links between any two
    entities (the future-graph edges). Pick each side's type + paste its UUID.
    """

    list_display = ("subject", "predicate", "object", "created_at")
    list_filter = ("predicate", "subject_content_type", "object_content_type")
    search_fields = ("predicate",)
    fields = (
        ("subject_content_type", "subject_object_id"),
        "predicate",
        ("object_content_type", "object_object_id"),
        "metadata",
    )

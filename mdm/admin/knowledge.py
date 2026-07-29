"""Admin for Document / Knowledge Asset."""

from django.contrib import admin

from core.admin import BaseModelAdmin, IdentifierInline
from mdm.models import Document


@admin.register(Document)
class DocumentAdmin(BaseModelAdmin):
    list_display = ("title", "doc_type", "visibility", "version", "owner", "updated_at")
    search_fields = ("title", "version")
    list_filter = ("doc_type", "visibility", "topics")
    autocomplete_fields = ("doc_type", "authors", "topics", "owner")
    list_select_related = ("doc_type", "owner")
    inlines = [IdentifierInline]
    fieldsets = (
        (None, {"fields": ("title", "doc_type", "url", "version")}),
        ("Authorship & subjects", {"fields": ("authors", "author_names", "topics", "mentions")}),
        ("References", {"fields": ("citations",)}),
        ("AI / embeddings", {"classes": ("collapse",), "fields": ("embedding_model", "embedding")}),
        ("Access control", {"fields": ("visibility", "owner", "permissions")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

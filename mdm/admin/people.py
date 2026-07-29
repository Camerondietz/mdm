"""Admin for Person."""

from django.contrib import admin

from core.admin import BaseModelAdmin, ContactPointInline, IdentifierInline
from mdm.models import Employment, Person


class PersonEmploymentInline(admin.TabularInline):
    """Show (and edit) this person's jobs right on their page."""

    model = Employment
    fk_name = "person"
    extra = 0
    autocomplete_fields = ("organization", "department", "employment_type", "manager")
    fields = (
        "organization",
        "job_title",
        "department",
        "employment_type",
        "start_date",
        "end_date",
        "is_primary",
    )
    show_change_link = True
    verbose_name = "employment"
    verbose_name_plural = "employment / roles"


@admin.register(Person)
class PersonAdmin(BaseModelAdmin):
    list_display = ("name_col", "email_col", "phone_col", "birth_date", "updated_at")
    search_fields = ("full_name", "given_name", "family_name", "additional_name")
    list_filter = ("roles", "skills")
    autocomplete_fields = ("primary_location", "parents", "roles", "skills")
    inlines = [ContactPointInline, IdentifierInline, PersonEmploymentInline]
    fieldsets = (
        (
            "Name",
            {
                "fields": (
                    ("honorific_prefix", "given_name"),
                    ("additional_name", "family_name", "honorific_suffix"),
                    "full_name",
                    "aliases",
                )
            },
        ),
        ("Personal", {"fields": ("birth_date", "primary_location")}),
        ("Classification & relationships", {"fields": ("roles", "skills", "parents")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("contacts")

    @admin.display(description="Name", ordering="full_name")
    def name_col(self, obj):
        return str(obj)

    @admin.display(description="Email")
    def email_col(self, obj):
        for c in obj.contacts.all():
            if c.kind == "email":
                return c.value
        return "—"

    @admin.display(description="Phone")
    def phone_col(self, obj):
        for c in obj.contacts.all():
            if c.kind in ("phone", "mobile"):
                return c.value
        return "—"

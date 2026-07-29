"""Admin for Organization, Department, and Employment."""

from django.contrib import admin

from core.admin import BaseModelAdmin, ContactPointInline, IdentifierInline
from mdm.models import Department, Employment, Organization


class DepartmentInline(admin.TabularInline):
    model = Department
    fk_name = "organization"
    extra = 0
    fields = ("name", "parent", "description")
    autocomplete_fields = ("parent",)
    show_change_link = True


class OrgEmploymentInline(admin.TabularInline):
    """Every person employed by this organization, editable inline."""

    model = Employment
    fk_name = "organization"
    extra = 0
    autocomplete_fields = ("person", "department", "employment_type", "manager")
    fields = (
        "person",
        "job_title",
        "department",
        "employment_type",
        "start_date",
        "end_date",
        "is_primary",
    )
    show_change_link = True
    verbose_name = "employee"
    verbose_name_plural = "employees"


@admin.register(Organization)
class OrganizationAdmin(BaseModelAdmin):
    list_display = ("name", "org_type", "parent", "website", "employee_count")
    search_fields = ("name", "legal_name")
    list_filter = ("org_type",)
    autocomplete_fields = ("org_type", "parent", "primary_location", "locations")
    list_select_related = ("org_type", "parent")
    inlines = [ContactPointInline, IdentifierInline, DepartmentInline, OrgEmploymentInline]
    fieldsets = (
        (None, {"fields": ("name", "legal_name", "org_type", "parent", "website")}),
        ("Locations", {"fields": ("primary_location", "locations")}),
        ("Ownership & matching", {"fields": ("ownership", "domains")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

    @admin.display(description="Employees")
    def employee_count(self, obj):
        return obj.current_employees.count()


@admin.register(Department)
class DepartmentAdmin(BaseModelAdmin):
    list_display = ("name", "organization", "parent")
    search_fields = ("name", "description")
    list_filter = ("organization",)
    autocomplete_fields = ("organization", "parent")
    list_select_related = ("organization", "parent")
    inlines = [ContactPointInline, IdentifierInline]
    fieldsets = (
        (None, {"fields": ("name", "organization", "parent", "description")}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )


@admin.register(Employment)
class EmploymentAdmin(BaseModelAdmin):
    list_display = (
        "person",
        "job_title",
        "organization",
        "department",
        "is_current_col",
        "is_primary",
    )
    search_fields = ("job_title", "work_email", "person__full_name", "organization__name")
    list_filter = ("employment_type", "is_primary", "organization")
    autocomplete_fields = (
        "person",
        "organization",
        "department",
        "employment_type",
        "manager",
        "office_location",
    )
    list_select_related = ("person", "organization", "department")
    fieldsets = (
        ("Role", {"fields": ("person", "organization", "department", "job_title", "employment_type", "manager")}),
        ("Dates", {"fields": (("start_date", "end_date"), "is_primary")}),
        ("Business contact", {"fields": ("work_email", "extension", ("office", "office_location"))}),
        BaseModelAdmin.PROVENANCE_FIELDSET,
    )

    @admin.display(description="Current", boolean=True)
    def is_current_col(self, obj):
        return obj.is_current

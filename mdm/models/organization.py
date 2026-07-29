"""Organization and Department (schema.org ``Organization``)."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import BaseModel, ContactPoint, Identifier


class Organization(BaseModel):
    schema_type = "Organization"

    name = models.CharField(max_length=255, help_text="Common / trading name.")
    legal_name = models.CharField(max_length=255, blank=True, default="")
    org_type = models.ForeignKey(
        "mdm.OrganizationType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organizations",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subsidiaries",
        help_text="Parent company (this org is a subsidiary of it).",
    )
    website = models.URLField(blank=True, default="")

    # ── Locations ─────────────────────────────────────────────────────────────
    primary_location = models.ForeignKey(
        "mdm.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="headquartered_organizations",
        help_text="Headquarters / primary address.",
    )
    locations = models.ManyToManyField(
        "mdm.Location", blank=True, related_name="located_organizations"
    )

    # ── Structured extras ─────────────────────────────────────────────────────
    ownership = models.JSONField(
        default=dict,
        blank=True,
        help_text='Ownership structure, e.g. {"Acme Holdings": 60, "Founders": 40}.',
    )
    domains = models.JSONField(
        default=list,
        blank=True,
        help_text='Web/email domains used for record matching, e.g. ["acme.com"].',
    )

    contacts = GenericRelation(ContactPoint)
    identifiers = GenericRelation(Identifier)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["legal_name"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def current_employees(self):
        from mdm.models.person import Person

        return Person.objects.filter(
            employments__organization=self, employments__end_date__isnull=True
        ).distinct()

    def jsonld_properties(self) -> dict:
        props: dict = {
            "name": self.name,
            "legalName": self.legal_name,
            "url": self.website,
        }
        if self.parent_id:
            props["parentOrganization"] = self.parent.get_uri()
        if self.primary_location_id:
            props["address"] = self.primary_location.get_uri()
        subs = [s.get_uri() for s in self.subsidiaries.all()]
        if subs:
            props["subOrganization"] = subs
        depts = [d.get_uri() for d in self.departments.all()]
        if depts:
            props["department"] = depts
        return props


class Department(BaseModel):
    """A unit within an Organization; may nest via ``parent`` (schema.org sub-organization)."""

    schema_type = "Organization"

    organization = models.ForeignKey(
        "mdm.Organization", on_delete=models.CASCADE, related_name="departments"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    contacts = GenericRelation(ContactPoint)
    identifiers = GenericRelation(Identifier)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["organization", "name"])]

    def __str__(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        return f"{self.name} · {self.organization.name}"

    @property
    def current_employees(self):
        from mdm.models.person import Person

        return Person.objects.filter(
            employments__department=self, employments__end_date__isnull=True
        ).distinct()

    def jsonld_properties(self) -> dict:
        props: dict = {"name": self.name, "description": self.description}
        if self.organization_id:
            props["parentOrganization"] = self.organization.get_uri()
        return props

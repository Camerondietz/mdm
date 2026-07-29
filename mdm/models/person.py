"""Person: an individual (schema.org ``Person``).

Personal/identity data only. A Person's connection to organizations, departments,
job titles and managers is business data and lives on ``Employment``.
"""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import BaseModel, ContactPoint, Identifier


class Person(BaseModel):
    schema_type = "Person"

    # ── Name (schema.org name components) ─────────────────────────────────────
    honorific_prefix = models.CharField(max_length=50, blank=True, default="", help_text="e.g. Dr., Ms.")
    given_name = models.CharField(max_length=120, blank=True, default="", help_text="First name.")
    additional_name = models.CharField(max_length=120, blank=True, default="", help_text="Middle name(s).")
    family_name = models.CharField(max_length=120, blank=True, default="", help_text="Last name.")
    honorific_suffix = models.CharField(max_length=50, blank=True, default="", help_text="e.g. Jr., PhD.")
    full_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Display name. Auto-filled from name parts if left blank.",
    )
    aliases = models.JSONField(
        default=list, blank=True, help_text="Alternate names / nicknames (list of strings)."
    )

    # ── Personal ──────────────────────────────────────────────────────────────
    birth_date = models.DateField(null=True, blank=True, help_text="Date of birth.")
    primary_location = models.ForeignKey(
        "mdm.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="residents",
    )

    # ── Relationships / classification ────────────────────────────────────────
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True
    )
    roles = models.ManyToManyField("mdm.Role", blank=True, related_name="people")
    skills = models.ManyToManyField("mdm.Skill", blank=True, related_name="people")

    # ── Contact endpoints & external identifiers (generic) ────────────────────
    contacts = GenericRelation(ContactPoint)
    identifiers = GenericRelation(Identifier)

    class Meta:
        ordering = ["family_name", "given_name"]
        verbose_name = "person"
        verbose_name_plural = "people"
        indexes = [
            models.Index(fields=["family_name", "given_name"]),
            models.Index(fields=["full_name"]),
        ]

    # ── Naming ────────────────────────────────────────────────────────────────
    @property
    def computed_name(self) -> str:
        parts = [
            self.honorific_prefix,
            self.given_name,
            self.additional_name,
            self.family_name,
            self.honorific_suffix,
        ]
        return " ".join(p for p in parts if p).strip()

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.computed_name
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name or self.computed_name or "(unnamed person)"

    @property
    def display_name(self) -> str:
        return str(self)

    # ── Convenience accessors ─────────────────────────────────────────────────
    def _primary_contact(self, kind: str) -> str:
        cp = self.contacts.filter(kind=kind).order_by("-is_primary").first()
        return cp.value if cp else ""

    @property
    def primary_email(self) -> str:
        return self._primary_contact(ContactPoint.Kind.EMAIL)

    @property
    def primary_phone(self) -> str:
        return self._primary_contact(ContactPoint.Kind.PHONE)

    @property
    def organizations(self):
        """Distinct organizations this person is/was employed by."""
        from mdm.models.organization import Organization

        return Organization.objects.filter(employments__person=self).distinct()

    def jsonld_properties(self) -> dict:
        props: dict = {
            "name": str(self),
            "givenName": self.given_name,
            "additionalName": self.additional_name,
            "familyName": self.family_name,
            "honorificPrefix": self.honorific_prefix,
            "honorificSuffix": self.honorific_suffix,
            "alternateName": list(self.aliases or []),
            "birthDate": self.birth_date.isoformat() if self.birth_date else None,
            "email": self.primary_email,
            "telephone": self.primary_phone,
        }
        if self.primary_location_id:
            props["homeLocation"] = self.primary_location.get_uri()
        orgs = [o.get_uri() for o in self.organizations]
        if orgs:
            props["worksFor"] = orgs
        return props

"""Location: a hierarchical geographic entity (schema.org ``Place``)."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import BaseModel, Identifier


class Location(BaseModel):
    """
    A place at any level of geographic granularity — from a country down to a
    single street address or GPS point — linked into a hierarchy via ``parent``.
    Persons and Organizations reference Locations rather than copying address text,
    so an address is mastered once and reused everywhere (stable IDs).
    """

    schema_type = "Place"

    class Kind(models.TextChoices):
        COUNTRY = "country", "Country"
        REGION = "region", "Region"
        STATE = "state", "State / Province"
        COUNTY = "county", "County"
        CITY = "city", "City / Locality"
        DISTRICT = "district", "District / Neighborhood"
        ADDRESS = "address", "Street address"
        POINT = "point", "Point / Coordinates"
        VIRTUAL = "virtual", "Virtual / Online"

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.ADDRESS)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        help_text="Containing place (e.g. a City's parent is a State).",
    )

    # ── Structured postal address (schema.org PostalAddress) ──────────────────
    street_address = models.CharField(max_length=255, blank=True, default="")
    address_locality = models.CharField(max_length=120, blank=True, default="", help_text="City / town.")
    address_region = models.CharField(max_length=120, blank=True, default="", help_text="State / province.")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    country_code = models.CharField(
        max_length=2, blank=True, default="", help_text="ISO 3166-1 alpha-2 country code, e.g. US."
    )

    # ── Coordinates ───────────────────────────────────────────────────────────
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # ── Stable external code (ISO, UN/LOCODE, GeoNames id, ...) ────────────────
    code = models.CharField(max_length=64, blank=True, default="")

    identifiers = GenericRelation(Identifier)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["kind"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["postal_code"]),
        ]

    def __str__(self) -> str:
        return self.full_path

    @property
    def display_name(self) -> str:
        return self.full_path

    @property
    def full_path(self) -> str:
        """Breadcrumb up the hierarchy, e.g. '1 Main St, Springfield, IL, US'."""
        parts, node, guard = [], self, 0
        while node is not None and guard < 12:
            parts.append(node.name)
            node = node.parent
            guard += 1
        return ", ".join(parts)

    @property
    def one_line_address(self) -> str:
        bits = [
            self.street_address,
            self.address_locality,
            self.address_region,
            self.postal_code,
            self.country_code,
        ]
        return ", ".join(b for b in bits if b)

    def jsonld_properties(self) -> dict:
        props: dict = {"name": self.name}
        if self.parent_id:
            props["containedInPlace"] = self.parent.get_uri()
        address = {
            k: v
            for k, v in {
                "@type": "PostalAddress",
                "streetAddress": self.street_address,
                "addressLocality": self.address_locality,
                "addressRegion": self.address_region,
                "postalCode": self.postal_code,
                "addressCountry": self.country_code,
            }.items()
            if v
        }
        if len(address) > 1:
            props["address"] = address
        if self.latitude is not None and self.longitude is not None:
            props["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": float(self.latitude),
                "longitude": float(self.longitude),
            }
        return props

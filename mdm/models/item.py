"""Item: a product, asset, SKU, or catalog entry (schema.org ``Product``)."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import BaseModel, Identifier


class Item(BaseModel):
    schema_type = "Product"

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=120, blank=True, default="", db_index=True)
    version = models.CharField(max_length=60, blank=True, default="")
    manufacturer = models.ForeignKey(
        "mdm.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manufactured_items",
    )
    categories = models.ManyToManyField("mdm.ItemCategory", blank=True, related_name="items")

    features = models.JSONField(
        default=dict,
        blank=True,
        help_text='Attribute/value pairs, e.g. {"color": "black", "weight_kg": 2.4}.',
    )
    pricing = models.JSONField(
        default=dict,
        blank=True,
        help_text='Price info, e.g. {"currency": "USD", "price": 199.0, "type": "list"}.',
    )
    documents = models.ManyToManyField(
        "mdm.Document", blank=True, related_name="items", help_text="Manuals, specs, datasheets."
    )
    related_items = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="related_to"
    )

    identifiers = GenericRelation(Identifier)  # GTIN, UPC, MPN, ...

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}" if self.version else self.name

    @property
    def display_name(self) -> str:
        return str(self)

    def jsonld_properties(self) -> dict:
        props: dict = {
            "name": self.name,
            "sku": self.sku,
            "version": self.version,
            "category": [c.name for c in self.categories.all()],
            "additionalProperty": self.features or {},
        }
        if self.manufacturer_id:
            props["manufacturer"] = self.manufacturer.get_uri()
        if self.pricing:
            props["offers"] = {"@type": "Offer", **self.pricing}
        return props

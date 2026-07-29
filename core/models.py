"""
Shared infrastructure for every MDM entity.

Design goals (industry-standard / future-proof):
  * UUID primary keys + stable URIs  -> globally unique, mergeable IDs.
  * JSON-LD / Schema.org serialization -> canonical, AI-interoperable data model.
  * MDM provenance (source_system)    -> track the system of record per record.
  * ``metadata`` JSONField            -> extend any entity with custom-ontology attrs
                                         without a schema migration.
  * Generic Identifier / ContactPoint / Relationship tables -> attach alternate IDs,
    contact endpoints, and typed cross-entity links to ANY model. ``Relationship`` is
    a subject-predicate-object triple: the bridge to a future graph model.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


# ══════════════════════════════════════════════════════════════════════════════
# Abstract base model
# ══════════════════════════════════════════════════════════════════════════════
class BaseModel(models.Model):
    """Abstract base every canonical entity inherits from."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── MDM provenance (which system this record was mastered from) ────────────
    source_system = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="System of record this entity was mastered from (MDM provenance).",
    )
    source_record_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Native primary key of this entity in its source system.",
    )

    # ── Extensibility (custom ontology / schema.org extension attributes) ──────
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Free-form structured attributes (custom ontology / schema.org extensions).",
    )

    # Schema.org type used for JSON-LD @type. Subclasses override.
    schema_type: str = "Thing"
    jsonld_context: str = "https://schema.org"

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    # ── Identity / URIs ───────────────────────────────────────────────────────
    def get_uri(self) -> str:
        """Stable, resolvable URI used as the JSON-LD @id."""
        base = str(getattr(settings, "MDM_BASE_URI", "https://mdm.local")).rstrip("/")
        return f"{base}/id/{self._meta.model_name}/{self.pk}"

    @property
    def display_name(self) -> str:
        """Human label for search results / detail headers. Override as needed."""
        return str(self)

    # ── JSON-LD serialization ─────────────────────────────────────────────────
    def jsonld_properties(self) -> dict:
        """Return {schema.org property: JSON-serializable value}. Override per model."""
        return {}

    def to_jsonld(self) -> dict:
        """Serialize this entity as a JSON-LD document (schema.org vocabulary)."""
        data: dict = {
            "@context": self.jsonld_context,
            "@id": self.get_uri(),
            "@type": self.schema_type,
        }
        # Custom-ontology attributes first, explicit mappings win on conflict.
        if self.metadata:
            data.update(self.metadata)
        for key, value in self.jsonld_properties().items():
            if value not in (None, "", [], {}):
                data[key] = value
        return data


# ══════════════════════════════════════════════════════════════════════════════
# Generic, attach-to-anything value tables
# ══════════════════════════════════════════════════════════════════════════════
class Identifier(models.Model):
    """
    Alternate / external identifier for any entity (schema.org ``identifier`` /
    ``PropertyValue``). E.g. DUNS, EIN, LEI, ISBN, GTIN, DOI, SSN, or an internal key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    entity = GenericForeignKey("content_type", "object_id")

    scheme = models.CharField(
        max_length=64,
        help_text="Identifier scheme, e.g. DUNS, EIN, LEI, ISBN, GTIN, DOI, SSN, internal.",
    )
    value = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["scheme", "value"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "scheme", "value"],
                name="uniq_identifier_per_entity",
            )
        ]

    def __str__(self) -> str:
        return f"{self.scheme}: {self.value}"


class ContactPoint(models.Model):
    """
    A contact endpoint (email / phone / social / website) for any entity
    (schema.org ``ContactPoint``). Covers Person emails/phones/socials,
    Organization phone/website, Department contact info, etc.
    """

    class Kind(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        MOBILE = "mobile", "Mobile"
        FAX = "fax", "Fax"
        WEBSITE = "website", "Website"
        SOCIAL = "social", "Social profile"
        MESSAGING = "messaging", "Messaging / IM"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    entity = GenericForeignKey("content_type", "object_id")

    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.EMAIL)
    value = models.CharField(max_length=320, help_text="Email address, phone number, URL, or handle.")
    label = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Context label, e.g. work, home, billing, LinkedIn.",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "kind"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["kind", "value"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.value}"


class Relationship(models.Model):
    """
    A directed, typed relationship between any two entities, stored as a
    subject-predicate-object triple. This is the relational bridge to a future
    graph model — every edge in the eventual graph already lives here.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    subject_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    subject_object_id = models.UUIDField()
    subject = GenericForeignKey("subject_content_type", "subject_object_id")

    predicate = models.CharField(
        max_length=64,
        help_text="Relationship type, e.g. relatedTo, partOf, owns, memberOf, "
        "supersedes, dependsOn, mentions.",
    )

    object_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_object_id = models.UUIDField()
    object = GenericForeignKey("object_content_type", "object_object_id")

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["subject_content_type", "subject_object_id"]),
            models.Index(fields=["object_content_type", "object_object_id"]),
            models.Index(fields=["predicate"]),
        ]

    def __str__(self) -> str:
        return f"{self.subject} —[{self.predicate}]→ {self.object}"


# ══════════════════════════════════════════════════════════════════════════════
# Taxonomy / controlled-vocabulary base (SKOS-inspired)
# ══════════════════════════════════════════════════════════════════════════════
class TaxonomyTerm(models.Model):
    """
    Abstract base for hierarchical controlled-vocabulary tables (organization
    types, employment types, item categories, document types, roles, skills,
    topics, ...). Inspired by SKOS: a term has a broader/narrower (parent/child)
    relationship and a stable code.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    code = models.CharField(
        max_length=64, blank=True, default="", help_text="Stable external code for this term."
    )
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

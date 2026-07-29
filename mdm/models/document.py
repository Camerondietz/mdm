"""Document / Knowledge Asset (schema.org ``CreativeWork``)."""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import BaseModel, Identifier


class Document(BaseModel):
    schema_type = "CreativeWork"

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        RESTRICTED = "restricted", "Restricted"
        INTERNAL = "internal", "Internal"
        PUBLIC = "public", "Public"

    title = models.CharField(max_length=255)
    doc_type = models.ForeignKey(
        "mdm.DocumentType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    authors = models.ManyToManyField(
        "mdm.Person", blank=True, related_name="authored_documents"
    )
    author_names = models.JSONField(
        default=list, blank=True, help_text="External authors not in the Person table (list of names)."
    )
    topics = models.ManyToManyField("mdm.Topic", blank=True, related_name="documents")
    mentions = models.JSONField(
        default=list,
        blank=True,
        help_text="Entities mentioned (names or URIs). Use Relationships for formal links.",
    )

    version = models.CharField(max_length=60, blank=True, default="")
    citations = models.JSONField(
        default=list, blank=True, help_text="Citations / references (list of strings or URIs)."
    )
    url = models.URLField(blank=True, default="", help_text="Canonical location of the asset.")

    # ── AI interoperability ───────────────────────────────────────────────────
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text="Vector embedding as a JSON array. Migrate to pgvector for similarity search at scale.",
    )
    embedding_model = models.CharField(
        max_length=120, blank=True, default="", help_text="Model that produced the embedding."
    )

    # ── Access control ────────────────────────────────────────────────────────
    visibility = models.CharField(
        max_length=16, choices=Visibility.choices, default=Visibility.INTERNAL
    )
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Fine-grained ACL, e.g. {"groups": ["finance"], "roles": ["admin"]}.',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_documents",
    )

    identifiers = GenericRelation(Identifier)  # DOI, ISBN, ...

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["visibility"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def display_name(self) -> str:
        return self.title

    @property
    def all_author_names(self) -> list[str]:
        return [str(a) for a in self.authors.all()] + list(self.author_names or [])

    def jsonld_properties(self) -> dict:
        return {
            "name": self.title,
            "version": self.version,
            "url": self.url,
            "author": self.all_author_names,
            "about": [t.name for t in self.topics.all()],
            "mentions": list(self.mentions or []),
            "citation": list(self.citations or []),
            "dateCreated": self.created_at.isoformat() if self.created_at else None,
            "dateModified": self.updated_at.isoformat() if self.updated_at else None,
        }

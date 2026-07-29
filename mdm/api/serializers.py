"""DRF serializers for the MDM API.

Each entity has a writable base serializer (foreign keys as UUID PKs) plus, where
useful, a richer *detail* serializer with nested reads — e.g. an Organization's
departments and employees, or a Person's employment history and contact points.
Every serializer exposes the stable ``uri`` (JSON-LD @id) and a human ``label``.
"""

from __future__ import annotations

from rest_framework import serializers

from core.models import ContactPoint, Identifier, Relationship
from mdm.models import (
    Department,
    Document,
    DocumentType,
    Employment,
    EmploymentType,
    Item,
    ItemCategory,
    Location,
    Organization,
    OrganizationType,
    Person,
    Role,
    Skill,
    Topic,
)

AUDIT_FIELDS = ["source_system", "source_record_id", "metadata", "created_at", "updated_at"]
AUDIT_READONLY = ["created_at", "updated_at"]


# ── Generic attach-to-anything tables ─────────────────────────────────────────
class ContactPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPoint
        fields = ["id", "content_type", "object_id", "kind", "value", "label", "is_primary"]


class IdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identifier
        fields = ["id", "content_type", "object_id", "scheme", "value", "issuer", "is_primary"]


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relationship
        fields = [
            "id",
            "subject_content_type",
            "subject_object_id",
            "predicate",
            "object_content_type",
            "object_object_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["created_at"]


# ── Taxonomy ──────────────────────────────────────────────────────────────────
TERM_FIELDS = ["id", "name", "slug", "code", "description", "parent", "metadata"]


class _TermSerializer(serializers.ModelSerializer):
    class Meta:
        fields = TERM_FIELDS
        read_only_fields = ["id"]


def _term_serializer(model_cls):
    meta = type("Meta", (_TermSerializer.Meta,), {"model": model_cls})
    return type(f"{model_cls.__name__}Serializer", (_TermSerializer,), {"Meta": meta})


OrganizationTypeSerializer = _term_serializer(OrganizationType)
EmploymentTypeSerializer = _term_serializer(EmploymentType)
ItemCategorySerializer = _term_serializer(ItemCategory)
DocumentTypeSerializer = _term_serializer(DocumentType)
RoleSerializer = _term_serializer(Role)
SkillSerializer = _term_serializer(Skill)
TopicSerializer = _term_serializer(Topic)


# ── Location ──────────────────────────────────────────────────────────────────
class LocationSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")

    class Meta:
        model = Location
        fields = [
            "id",
            "uri",
            "label",
            "name",
            "kind",
            "parent",
            "street_address",
            "address_locality",
            "address_region",
            "postal_code",
            "country_code",
            "latitude",
            "longitude",
            "code",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


# ── Department & Employment ───────────────────────────────────────────────────
class DepartmentSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")

    class Meta:
        model = Department
        fields = ["id", "uri", "name", "organization", "parent", "description"] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


class EmploymentSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")
    is_current = serializers.ReadOnlyField()

    class Meta:
        model = Employment
        fields = [
            "id",
            "uri",
            "label",
            "person",
            "organization",
            "department",
            "job_title",
            "employment_type",
            "manager",
            "start_date",
            "end_date",
            "work_email",
            "extension",
            "office",
            "office_location",
            "is_primary",
            "is_current",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


# ── Person ────────────────────────────────────────────────────────────────────
class PersonSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")

    class Meta:
        model = Person
        fields = [
            "id",
            "uri",
            "label",
            "honorific_prefix",
            "given_name",
            "additional_name",
            "family_name",
            "honorific_suffix",
            "full_name",
            "aliases",
            "birth_date",
            "primary_location",
            "parents",
            "roles",
            "skills",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


class PersonDetailSerializer(PersonSerializer):
    contacts = ContactPointSerializer(many=True, read_only=True)
    identifiers = IdentifierSerializer(many=True, read_only=True)
    employments = EmploymentSerializer(many=True, read_only=True)

    class Meta(PersonSerializer.Meta):
        fields = PersonSerializer.Meta.fields + ["contacts", "identifiers", "employments"]


# ── Organization ──────────────────────────────────────────────────────────────
class OrganizationSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")

    class Meta:
        model = Organization
        fields = [
            "id",
            "uri",
            "label",
            "name",
            "legal_name",
            "org_type",
            "parent",
            "website",
            "primary_location",
            "locations",
            "ownership",
            "domains",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


class OrganizationDetailSerializer(OrganizationSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    employments = EmploymentSerializer(many=True, read_only=True)
    contacts = ContactPointSerializer(many=True, read_only=True)
    identifiers = IdentifierSerializer(many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + [
            "departments",
            "employments",
            "contacts",
            "identifiers",
        ]


# ── Item ──────────────────────────────────────────────────────────────────────
class ItemSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")

    class Meta:
        model = Item
        fields = [
            "id",
            "uri",
            "label",
            "name",
            "sku",
            "version",
            "manufacturer",
            "categories",
            "features",
            "pricing",
            "documents",
            "related_items",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


class ItemDetailSerializer(ItemSerializer):
    identifiers = IdentifierSerializer(many=True, read_only=True)

    class Meta(ItemSerializer.Meta):
        fields = ItemSerializer.Meta.fields + ["identifiers"]


# ── Document ──────────────────────────────────────────────────────────────────
class DocumentSerializer(serializers.ModelSerializer):
    uri = serializers.ReadOnlyField(source="get_uri")
    label = serializers.ReadOnlyField(source="display_name")

    class Meta:
        model = Document
        fields = [
            "id",
            "uri",
            "label",
            "title",
            "doc_type",
            "authors",
            "author_names",
            "topics",
            "mentions",
            "version",
            "citations",
            "url",
            "embedding",
            "embedding_model",
            "visibility",
            "permissions",
            "owner",
        ] + AUDIT_FIELDS
        read_only_fields = AUDIT_READONLY


class DocumentDetailSerializer(DocumentSerializer):
    identifiers = IdentifierSerializer(many=True, read_only=True)

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ["identifiers"]

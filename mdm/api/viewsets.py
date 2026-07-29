"""DRF viewsets exposing every entity for retrieve / create / update / delete.

Auth: token (external systems) or session (browsable API). Reads require login;
writes require the matching Django model permission (add/change/delete) — grant
these per-user or per-group in the admin. Each entity also serves canonical
JSON-LD at ``<detail-url>/jsonld/``.
"""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import ContactPoint, Identifier, Relationship
from mdm.api import serializers as s
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


class JSONLDMixin:
    """Adds a `/jsonld/` detail route returning the schema.org JSON-LD document."""

    @action(detail=True, methods=["get"])
    def jsonld(self, request, pk=None):
        return Response(self.get_object().to_jsonld())


# ── Core entities ─────────────────────────────────────────────────────────────
class PersonViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = (
        Person.objects.all()
        .select_related("primary_location")
        .prefetch_related("roles", "skills", "contacts", "identifiers", "employments")
    )
    serializer_class = s.PersonSerializer
    filterset_fields = ["roles", "skills", "primary_location", "source_system"]
    search_fields = ["full_name", "given_name", "family_name", "additional_name"]
    ordering_fields = ["full_name", "family_name", "created_at", "updated_at"]

    def get_serializer_class(self):
        return s.PersonDetailSerializer if self.action == "retrieve" else s.PersonSerializer


class OrganizationViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = (
        Organization.objects.all()
        .select_related("org_type", "parent", "primary_location")
        .prefetch_related("departments", "employments", "contacts", "identifiers")
    )
    serializer_class = s.OrganizationSerializer
    filterset_fields = ["org_type", "parent", "primary_location", "source_system"]
    search_fields = ["name", "legal_name"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return s.OrganizationDetailSerializer
        return s.OrganizationSerializer


class DepartmentViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related("organization", "parent")
    serializer_class = s.DepartmentSerializer
    filterset_fields = ["organization", "parent"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class EmploymentViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = Employment.objects.all().select_related(
        "person", "organization", "department", "employment_type", "manager"
    )
    serializer_class = s.EmploymentSerializer
    filterset_fields = ["person", "organization", "department", "employment_type", "is_primary"]
    search_fields = ["job_title", "work_email", "person__full_name", "organization__name"]
    ordering_fields = ["start_date", "end_date", "created_at"]


class ItemViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = (
        Item.objects.all()
        .select_related("manufacturer")
        .prefetch_related("categories", "documents", "related_items", "identifiers")
    )
    serializer_class = s.ItemSerializer
    filterset_fields = ["manufacturer", "categories", "source_system"]
    search_fields = ["name", "sku", "version"]
    ordering_fields = ["name", "sku", "created_at", "updated_at"]

    def get_serializer_class(self):
        return s.ItemDetailSerializer if self.action == "retrieve" else s.ItemSerializer


class DocumentViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = (
        Document.objects.all()
        .select_related("doc_type", "owner")
        .prefetch_related("authors", "topics", "identifiers")
    )
    serializer_class = s.DocumentSerializer
    filterset_fields = ["doc_type", "topics", "authors", "visibility", "source_system"]
    search_fields = ["title", "version"]
    ordering_fields = ["title", "created_at", "updated_at"]

    def get_serializer_class(self):
        return s.DocumentDetailSerializer if self.action == "retrieve" else s.DocumentSerializer


class LocationViewSet(JSONLDMixin, viewsets.ModelViewSet):
    queryset = Location.objects.all().select_related("parent").prefetch_related("identifiers")
    serializer_class = s.LocationSerializer
    filterset_fields = ["kind", "country_code", "parent"]
    search_fields = ["name", "address_locality", "address_region", "postal_code", "code"]
    ordering_fields = ["name", "created_at"]


# ── Generic attach-to-anything tables ─────────────────────────────────────────
class ContactPointViewSet(viewsets.ModelViewSet):
    queryset = ContactPoint.objects.all()
    serializer_class = s.ContactPointSerializer
    filterset_fields = ["kind", "content_type", "object_id", "is_primary"]
    search_fields = ["value", "label"]


class IdentifierViewSet(viewsets.ModelViewSet):
    queryset = Identifier.objects.all()
    serializer_class = s.IdentifierSerializer
    filterset_fields = ["scheme", "content_type", "object_id", "is_primary"]
    search_fields = ["value", "issuer", "scheme"]


class RelationshipViewSet(viewsets.ModelViewSet):
    queryset = Relationship.objects.all()
    serializer_class = s.RelationshipSerializer
    filterset_fields = ["predicate", "subject_content_type", "object_content_type"]
    search_fields = ["predicate"]


# ── Taxonomy viewsets (generated) ─────────────────────────────────────────────
def _term_viewset(model_cls, serializer_cls):
    return type(
        f"{model_cls.__name__}ViewSet",
        (viewsets.ModelViewSet,),
        {
            "queryset": model_cls.objects.all().select_related("parent"),
            "serializer_class": serializer_cls,
            "filterset_fields": ["parent"],
            "search_fields": ["name", "code", "slug", "description"],
            "ordering_fields": ["name", "code"],
        },
    )


OrganizationTypeViewSet = _term_viewset(OrganizationType, s.OrganizationTypeSerializer)
EmploymentTypeViewSet = _term_viewset(EmploymentType, s.EmploymentTypeSerializer)
ItemCategoryViewSet = _term_viewset(ItemCategory, s.ItemCategorySerializer)
DocumentTypeViewSet = _term_viewset(DocumentType, s.DocumentTypeSerializer)
RoleViewSet = _term_viewset(Role, s.RoleSerializer)
SkillViewSet = _term_viewset(Skill, s.SkillSerializer)
TopicViewSet = _term_viewset(Topic, s.TopicSerializer)

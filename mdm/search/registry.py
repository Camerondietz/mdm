"""
Registry of entities exposed through the unified search page.

Adding a new searchable entity is a one-liner here — the search view, filters,
and result rendering all read from this list. ``vector_fields`` are the text
columns fed to PostgreSQL full-text search (stemmed, ranked). To move to
OpenSearch later, keep this registry and swap the query engine in ``views.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from mdm.models import (
    Department,
    Document,
    Employment,
    Item,
    Location,
    Organization,
    Person,
)


@dataclass(frozen=True)
class SearchSpec:
    key: str
    label: str
    icon: str
    model: type
    vector_fields: list[str]
    detail_route: str
    base_queryset: Callable = field(default=lambda model: model.objects.all())
    subtitle: Callable = field(default=lambda obj: "")

    def title(self, obj) -> str:
        return obj.display_name


SEARCH_SPECS: list[SearchSpec] = [
    SearchSpec(
        key="person",
        label="People",
        icon="👤",
        model=Person,
        vector_fields=["full_name", "given_name", "additional_name", "family_name"],
        detail_route="search:person_detail",
        base_queryset=lambda m: m.objects.select_related("primary_location").prefetch_related("contacts"),
        subtitle=lambda o: o.primary_email or (o.primary_location.full_path if o.primary_location_id else ""),
    ),
    SearchSpec(
        key="organization",
        label="Organizations",
        icon="🏢",
        model=Organization,
        vector_fields=["name", "legal_name", "website"],
        detail_route="search:organization_detail",
        base_queryset=lambda m: m.objects.select_related("org_type"),
        subtitle=lambda o: (o.org_type.name if o.org_type_id else "") or o.website,
    ),
    SearchSpec(
        key="department",
        label="Departments",
        icon="🗂️",
        model=Department,
        vector_fields=["name", "description", "organization__name"],
        detail_route="search:department_detail",
        base_queryset=lambda m: m.objects.select_related("organization"),
        subtitle=lambda o: o.organization.name,
    ),
    SearchSpec(
        key="employment",
        label="Employment",
        icon="💼",
        model=Employment,
        vector_fields=["job_title", "work_email", "person__full_name", "organization__name"],
        detail_route="search:employment_detail",
        base_queryset=lambda m: m.objects.select_related("person", "organization", "department"),
        subtitle=lambda o: o.organization.name,
    ),
    SearchSpec(
        key="item",
        label="Items",
        icon="📦",
        model=Item,
        vector_fields=["name", "sku", "version"],
        detail_route="search:item_detail",
        base_queryset=lambda m: m.objects.select_related("manufacturer"),
        subtitle=lambda o: (f"SKU {o.sku}" if o.sku else "") or (o.manufacturer.name if o.manufacturer_id else ""),
    ),
    SearchSpec(
        key="document",
        label="Documents",
        icon="📄",
        model=Document,
        vector_fields=["title", "version"],
        detail_route="search:document_detail",
        base_queryset=lambda m: m.objects.select_related("doc_type"),
        subtitle=lambda o: o.doc_type.name if o.doc_type_id else o.get_visibility_display(),
    ),
    SearchSpec(
        key="location",
        label="Locations",
        icon="📍",
        model=Location,
        vector_fields=["name", "address_locality", "address_region", "postal_code", "code"],
        detail_route="search:location_detail",
        base_queryset=lambda m: m.objects.select_related("parent"),
        subtitle=lambda o: o.one_line_address or o.get_kind_display(),
    ),
]

SPECS_BY_KEY = {spec.key: spec for spec in SEARCH_SPECS}
